import os
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
# from langchain_openai import OpenAIEmbeddings
import uuid
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain_openai import OpenAIEmbeddings,ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from services.scraper import scrape_all_websites
# from ..services.extractData import extract_text_from_pdfs, extract_data_from_csv, extract_data_from_excel

import time
load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY', '').strip(),
)

# Verify API key
def validate_openai_key():
    try:
        client.embeddings.create(
            input="Test embedding",
            model="text-embedding-ada-002"
        )
        print("OpenAI API key is valid!")
        return True
    except Exception as e:
        print(f"OpenAI API key validation failed: {e}")
        return False

# Enhanced OpenAI Embeddings with explicit client
embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv('OPENAI_API_KEY', '').strip(),
    model='text-embedding-ada-002',
    client=client  # Pass the explicitly created client
)
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))


index_name = "investing-rag"
existing_indexes = [index["name"] for index in pc.list_indexes()]
print(existing_indexes)
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI embeddings dimension
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
namespace="investing"
# Get the Pinecone index
index = pc.Index(index_name)

def get_embedding(text):
    try:
        # Direct OpenAI client call for embedding
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        

        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding generation error: {e}")
        return None


def upsert_vector(vectors, namespace):
    try:
        # Check if the index exists
        if index_name not in [index["name"] for index in pc.list_indexes()]:
            pc.create_index(
                name=index_name, 
                dimension=1536,  # OpenAI embeddings dimension
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print(f"Index '{index_name}' created successfully.")
        else:
            print(f"Index '{index_name}' already exists.")

        # Proceed to upsert vectors
        if vectors:
            index.upsert(vectors=vectors, namespace=namespace)
            print(f"Processed {len(vectors)} chunks.")
            return True
        return False

    except Exception as e:
        print(f"Error during upsert or index creation: {e}")
        return False

async def create_vectorstore(file_path):
    try:
        # Validate API key before processing
        if not validate_openai_key():
            raise ValueError("Cannot proceed without a valid OpenAI API key")

        # Get list of scraped company data
        company_data = scrape_all_websites(file_path)
            
        if not company_data:
            print("No text content extracted from file")
            return False

        namespace = "investing"
        successful_embeddings = False
        
        # Document processing
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )

        # Process each company's data separately
        for company_index, company_info in enumerate(company_data):
            print(f"\nProcessing company {company_index + 1}/{len(company_data)}")
            
            if not company_info.get('text'):  # Skip empty texts
                continue
                
            # Split this company's text into chunks
            text_chunks = text_splitter.split_text(company_info['text'])
            
            # Create Langchain documents for this company
            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        "source": company_info['company_name'],
                        "url": company_info['url'],
                        "chunk": i,
                        "company_index": company_index,
                    }
                ) for i, chunk in enumerate(text_chunks)
            ]

            print(f"Created {len(documents)} chunks for {company_info['company_name']}")
            
            vectors = []
            count = 0

            # Process chunks for this company
            for doc in documents:
                embedding = get_embedding(doc.page_content)
                if embedding is None:
                    continue
                
                vector_id = str(uuid.uuid4())

                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "text": doc.page_content,
                        "source": doc.metadata.get('source', ''),
                        "url": doc.metadata.get('url', ''),
                        "chunk": doc.metadata.get('chunk', 0),
                        "company_index": doc.metadata.get('company_index'),
                    }
                })
                
                # Perform upsert in batches
                count += 1
                if count >= 50:
                    is_batch_done = upsert_vector(vectors, namespace)
                    if is_batch_done:
                        successful_embeddings = True
                    print(f"Upsert batch completed for {doc.metadata['source']}: {is_batch_done}")
                    vectors = []
                    count = 0

            # Final batch upsert for this company
            if vectors:
                is_final_batch_done = upsert_vector(vectors, namespace)
                if is_final_batch_done:
                    successful_embeddings = True
                print(f"Final upsert completed for {company_info['company_name']}: {is_final_batch_done}")

        print(f"Vector store creation completed. Success: {successful_embeddings}")
        return successful_embeddings

    except Exception as e:
        print(f"Error in create_vectorstore: {str(e)}")
        return False
    
def retrieve_from_vectorstore(
    query, 
    index_name='investing-rag', 
    namespace='investing',
    top_k=25,  # Increased from 6 to 15
    include_metadata=True,
):
    embeddings = OpenAIEmbeddings(
        api_key=os.getenv('OPENAI_API_KEY')
    )
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    index = pc.Index(index_name)
    
    try:
        query_embedding = embeddings.embed_query(query)
        metadata_filter = {}
        
        search_results = index.query(
            namespace=namespace,
            vector=query_embedding,
            top_k=top_k,  # Increased number of results
            include_values=True,
            include_metadata=include_metadata,
            filter=metadata_filter
        )
        
        formatted_results = []
        print("\n=== Processing Search Results ===")
        for match in search_results.matches:
            if match.score >= 0.6:  # Lowered threshold from 0.7 to 0.6 for more results
                result = {
                    'score': match.score,
                    'text': match.metadata.get('text', ''),
                    'company_name': match.metadata.get('source', 'Unknown'),
                    'url': match.metadata.get('url', ''),
                    'chunk_number': match.metadata.get('chunk', -1)
                }
                formatted_results.append(result)
                print(f"Match Score: {match.score:.3f} - Company: {result['company_name']}")
            else:
                print(f"Skipping low-score match: {match.score:.3f}")
        
        # Sort results by score but don't limit the number of results
        formatted_results = sorted(formatted_results, key=lambda x: x['score'], reverse=True)
        print("Total formatted results:", len(formatted_results))
        
        return {
            'query': query,
            'total_results': len(formatted_results),
            'results': formatted_results
        }
    
    except Exception as e:
        print(f"Error retrieving from vectorstore: {e}")
        return {
            'query': query,
            'total_results': 0,
            'results': [],
            'error': str(e)
        }

def handle_context(query):
    try:
        results = retrieve_from_vectorstore(query=query['query'])
        
        print(f"\n-----Search Query: {results['query']}")
        print(f"\n-----Total Relevant Chunks: {results['total_results']}")
        
        sorted_results = sorted(results['results'], key=lambda x: x['score'], reverse=True)
        top_results = sorted_results  
        
        # Create structured context with company information
        structured_context = []
        for result in top_results:
            company_info = {
                'company_name': result['company_name'],
                'url': result['url'],
                'text': result['text']
            }
            structured_context.append(company_info)
        # Format the context as a string with clear company sections
        formatted_context = ""
        for info in structured_context:
            formatted_context += f"\nCOMPANY: {info['company_name']}\n"
            formatted_context += f"URL: {info['url']}\n"
            formatted_context += f"DETAILS: {info['text']}\n"
            formatted_context += "-" * 50 + "\n"  # Separator between companies
        
        return formatted_context
    
    
    except Exception as e:
        print(f"ERROR RETRIEVING CONTEXT: {e}") 
        return ""

async def search_documents(query):
    system_prompt = """
    You are an expert AI investor advisor specializing in matching startups with potential investors who can invest in their startup. Your task is to analyze the startup's profile and find the lists of investors from the provided context minimum 10 investors.
    you should not miss any company from the provided context if not Matching then add them at last section with a note explaining why it might still be slightly relevant.
    Added a friendly yet professional tone to the presentation.
    you will be showcasing the response as you are the one who is providing the list of investors for respective startup to the users who are looking for the investors for their startup
    Startup Profile:
    {query}

    The context contains information about potential investors, structured as:
    - Company/Investor Name (marked with "COMPANY:")
    - Website (marked with "URL:")
    - Detailed Information (marked with "DETAILS:")

    Rules:
    1. Format your response in professional Markdown with these sections:
       ## Investors Matched
       For each recommended investor:
       ### [Investor Name](url)
       - Investment Focus: Their main investment areas
       - Investment Stage: What stages they typically invest in
       - Investment Range: Typical investment amounts (if available)
       - Why They're a Good Match: Explain alignment with the startup's profile
       - Key Strengths: What unique value they bring 

    2. Matching Criteria:
       - Industry alignment with startup's sector
       - Stage compatibility (seed, early-stage, growth, etc.)
       - Investment amount range matching startup's needs
       - Strategic value beyond just funding

    3. Response Guidelines:
       - Recommend as many best-matching investors as possible
       - Keep total response between 200-400 words
       - Focus on quality matches over quantity
       - If no good matches found, explain why and suggest alternative approaches
       - Include direct URLs to investor websites
       - Highlight any specific relevant experience in startup's industry

    4. Format Example:
       ## Investors Matched

       ### [Sequoia Capital](https://sequoiacap.com)
       - # Investment Focus: Technology, Healthcare, Consumer
       - #Investment Stage: Series A to Growth
       - # Investment Range: $1M - $100M
       - # Why They're a Good Match: Strong track record in startup's industry
       - # Key Strengths: Global network, operational support
       - # Contact: add this field if you have any contact information for the investor

    5. Base all recommendations strictly on the provided context and strictly provide minimum 10 investors
    6. You must strictly privde all the Companies given in the context, Do not miss any company from the provided context. If a company is not highly relevant, include those in the last section at the end with a note explaining why it might still be slightly relevant.


    Additional Context: {retrieved_context}
    """

    user_data_template = """
    Format Instructions: Analyze the startup profile and provide matching investors in professional markdown format.

    Startup Profile to Match:
    {query}

    Remember: 
    - Focus on relevant matches based on industry, stage, and funding needs
    - Provide clear rationale for each recommendation
    - Include all URLs in proper markdown format
    - Structure the response professionally with clear sections and bullet points
    """

    generation_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(template=system_prompt),
        HumanMessagePromptTemplate.from_template(template=user_data_template),
    ])

    chat = ChatOpenAI(
        model='gpt-4',
        temperature=0.7,
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        streaming=True
    )

    try:
        context_results = handle_context({'query': query})
        augmented_query = {
            'query': query,
            'retrieved_context': context_results
        }
        messages = generation_prompt.format_messages(**augmented_query)
        return chat.astream(messages)
    except Exception as e:
        print(f"Error in search_documents: {e}")
        raise e

