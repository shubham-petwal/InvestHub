from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db, create_tables
from models import Base, Startup
import schemas
from fastapi.middleware.cors import CORSMiddleware
from services.scraper import scrape_all_websites
import os
from services.vectorstore import create_vectorstore, search_documents
from fastapi.responses import StreamingResponse
import json
from datetime import datetime
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Example endpoint using database
@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    return {"message": "Database connection successful"}

# @app.post("/findRelatedStartups", response_model=schemas.Startup)
# def find_related_startups(startup: schemas.StartupCreate, db: Session = Depends(get_db)):
#     try:
#         # Create a new Startup instance
#         db_startup = Startup(
#             company_name=startup.company_name,
#             industry=startup.industry,
#             stage=startup.stage,
#             funding_needed=startup.funding_needed,
#             description=startup.description
#         )
    
#         # Save to database
#         db.add(db_startup)
#         db.commit()
#         db.refresh(db_startup)
        
#         print("Received and Saved Startup Data:", {
#             "company_name": startup.company_name,
#             "industry": startup.industry,
#             "stage": startup.stage,
#             "funding_needed": startup.funding_needed,
#             "description": startup.description
#         })

#         return db_startup

#     except Exception as e:
#         db.rollback()  # Rollback the transaction in case of error
#         print(f"Error: {str(e)}")  # For debugging
#         raise HTTPException(status_code=500, detail=str(e)) 

@app.get("/startups", response_model=list[schemas.Startup])
def get_startups(db: Session = Depends(get_db)):
    startups = db.query(Startup).all()
    return startups 


# Add this class with the existing schemas
class FilePathRequest(BaseModel):
    file_path: str

@app.post("/store-vectors")
async def store_vectors(request: FilePathRequest):
    try:
        result = await create_vectorstore(request.file_path)
        if result:
            return {"message": "Successfully stored vectors", "status": "success"}
        return {"message": "Failed to store vectors", "status": "failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/search")
# async def search(query: str):
#     try:
#         # Create a chat stream with simplified parameters
#         chat_stream = await search_documents(
#             query=query,
#             dataSources=[],  # Empty since we're not filtering by data sources
#             prompt="Please provide a relevant answer based on the available information.",
#             model="gpt-3.5-turbo"  # You can change this to gpt-4 if needed
#         )
        
#         # Collect the response
#         response_text = ""
#         async for chunk in chat_stream:
#             if chunk.choices[0].delta.content is not None:
#                 response_text += chunk.choices[0].delta.content
        
#         return {"response": response_text}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e)) 

@app.post("/findRelatedStartups")
async def findRelatedStartups(
    data: schemas.SearchQueryRequest,
    db: Session = Depends(get_db)
):
    try:
        query = f'''
        I am representing {data.company_name}, a {data.stage} stage startup in the {data.industry} industry. 
        We are seeking investment of ${data.funding_needed:,} with a minimum ticket size of ${data.minimum_investment:,}. 
        We are offering {data.equity_offering}% equity and looking to close this round within {data.funding_timeline}. 
        The funds will primarily be used for {data.primary_use}.

        About us: {data.description}

        Based on our profile, please find the most suitable investors who:
        1. Have invested in {data.industry} sector
        2. Typically invest in {data.stage} stage companies
        3. Can invest between ${data.minimum_investment:,} to ${data.funding_needed:,}

        Please provide detailed information about each matching investor, including their investment focus, typical investment range, and why they would be a good fit for us.
        '''
        
        # Get the streaming chain
        stream = await search_documents(query)
        async def generate_chat_response():
            complete_response = []
            try:
                async for chunk in stream:
                    if hasattr(chunk, 'content'):
                        content = chunk.content
                        complete_response.append(content)
                        yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                
                # Send end of stream marker
                yield f"data: {json.dumps({'type': 'end', 'content': ''})}\n\n"

                # Store complete response if needed
                if complete_response:
                    try:
                        full_response = "".join(complete_response)
                        print("Full response:", full_response)
                        # Here you can add code to store the response in database
                        
                    except Exception as save_error:
                        print(f"Error saving to database: {str(save_error)}")

            except Exception as e:
                print(f"Streaming error: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
                yield f"data: {json.dumps({'type': 'end', 'content': ''})}\n\n"

        return StreamingResponse(
            generate_chat_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "X-Accel-Buffering": "no"  # Disable buffering in Nginx
            }
        )

    except Exception as e:
        print(f"Error in search endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        ) 