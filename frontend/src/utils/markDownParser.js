import DOMPurify from 'dompurify';

// Utility function to replace list markers, including nested lists
const replaceLists = (text, pattern, listClass) => {
  // Recursive function to handle nested lists
  const processList = (input) => {
    return input.replace(pattern, (match, indent, marker, content) => {
      const markdownLink = content.match(/\[(.*?)\]\((.*?)\)/);
      const plainUrl = content.match(/(https?:\/\/[^\s]+)/g);
      let listItem;

      if (markdownLink) {
        const cleanedUrl = markdownLink[2].replaceAll(' ', '');
        listItem = `<li class="${listClass}"><a href="${cleanedUrl}" target="_blank" class="text-primary hover:underline">${markdownLink[1]}</a></li>`;
      } else if (plainUrl) {
        listItem = `<li class="${listClass}"><a href="${plainUrl[0]}" target="_blank" class="text-primary hover:underline">${plainUrl[0]}</a></li>`;
      } else {
        listItem = `<li class="${listClass}">${content.trim()}</li>`;
      }

      return listItem;
    });
  };

  // Process the text to handle nested lists
  const lines = text.split(/\n/);
  let result = '';
  const stack = []; // Stack to keep track of current list tags

  lines.forEach(line => {
    const indentLevel = line.match(/^\s*/)[0].length; // Count leading spaces
    const isOrdered = /^\d+\./.test(line);
    const isUnordered = /^[*+-]/.test(line);
    const currentTag = isOrdered ? 'ol' : isUnordered ? 'ul' : null;

    // Adjust the stack for nested lists
    while (stack.length > indentLevel) {
      result += `</${stack.pop()}>\n`;
    }

    if (indentLevel === stack.length) {
      // Same level, just add the list item
      result += processList(line);
    } else if (indentLevel > stack.length) {
      // New nested list
      if (currentTag) {
        result += `<${currentTag}>\n`;
        stack.push(currentTag);
      }
      result += processList(line);
    } else {
      // Closing current list and starting a new one
      while (stack.length > indentLevel) {
        result += `</${stack.pop()}>\n`;
      }
      if (currentTag) {
        result += `<${currentTag}>\n`;
        stack.push(currentTag);
      }
      result += processList(line);
    }
  });
  // Close any remaining open lists
  while (stack.length) {
    result += `</${stack.pop()}>\n`;
  }

  return result.trim();
};

export const parseMarkdown = (text, customClasses = {}) => {
  // Escape raw HTML to prevent XSS
  text = DOMPurify.sanitize(text, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });

  // Handle headings
  text = text.replace(/^#{1,6} (.+)$/gm, (match, p1) => {
    const level = match.match(/^#{1,6}/)[0].length;
    return `<h${level} class="text-subtitle-2 font-weight-bold mb-1">${p1}</h${level}>`;
  });

  // Handle bold and italic text
  text = text
    .replace(/(\*\*|__)(.*?)\1/g, ' <strong class="font-weight-bold">$2</strong>')
    .replace(/(\*|_)(.*?)\1/g, ' <em class="font-italic">$2</em>');

  // Handle inline code
  text = text.replace(/`([^`]+)`/g, '<code class="bg-light-gray px-1 rounded">$1</code>');

  // Handle code blocks with language specification
  text = text.replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre class="bg-light-gray p-4 rounded"><code class="${lang ? `language-${lang}` : ''}">${code}</code></pre>`;
  });

  // Handle blockquotes
  text = text.replace(/^> (.*)$/gm, '<blockquote class="border-left-4 border-grey-400 pl-4 mb-1">$1</blockquote>');

  // Handle horizontal rules
  text = text.replace(/^(---|\*\*\*|___)$/gm, '<hr class="my-4 border-grey-400">');

  // Handle images
  text = text.replace(/!\[([^\]]*)\]\((.*?)\)/g, '<img src="$2" alt="$1" class="max-w-full h-auto"/>');

  // Handle links
  text = text.replace(/\[([^\]]+)\]\((.*?)\)/g, (match, textContent, url) => {
    const cleanedUrl = url.replaceAll(' ', '');
    return `<a href="${cleanedUrl}" target="_blank" class="text-primary hover:underline">${textContent}</a>`;
  });

  // Handle strikethrough text
  text = text.replace(/~~(.*?)~~/g, '<del>$1</del>');

  // Handle task lists
  text = text
    .replace(/^-\s*\[(x| )\](.*)$/gm, '<li class="list-disc ml-4"><input type="checkbox" checked="$1" class="mr-2">$2</li>')
    .replace(/<\/li>\n<li>/g, '</li><li>')
    .replace(/<\/li>\s*(<\/ul>|<\/ol>)/g, '</li>$1');
  text = '<ul class="mb-1">' + text + '</ul>';

  // Handle unordered and ordered lists
  text = replaceLists(text, /^(\s*)([*+-]|\d+\.)\s+(.*)/gm, 'list-disc ml-4');

  // Handle tables with alignment
  text = text.replace(/(\|.+\|\n)((?:\|[-:| ]+\|\n)+)((?:\|.*\|\n)*)/g, (match, header, separator, rows) => {
    const headers = header.trim().split('|').slice(1, -1).map(h => `<th class="border px-4 py-2">${h.trim()}</th>`).join('');
    const alignments = separator.trim().split('|').slice(1, -1).map(s => {
      if (s.trim().startsWith(':') && s.trim().endsWith(':')) return 'text-center';
      if (s.trim().startsWith(':')) return 'text-left';
      if (s.trim().endsWith(':')) return 'text-right';
      return '';
    });
    const rowsHtml = rows.trim().split('\n').map(row =>
      `<tr>${row.trim().split('|').slice(1, -1).map((cell, index) => `<td class="border px-4 py-2 ${alignments[index] || ''}">${cell.trim()}</td>`).join('')}</tr>`
    ).join('');
    return `<table class="min-w-full divide-y divide-gray-200"><thead><tr>${headers}</tr></thead><tbody>${rowsHtml}</tbody></table>`;
  });

  // Handle footnotes
  text = text.replace(/\[\^(\d+)\]:\s*(.*)/g, '<sup class="text-xs"><a href="#fn$1" id="ref$1">$1</a></sup>');
  text += (text.match(/\[\^(\d+)\]:\s*(.*)/g) || []).map(match => {
    const footnote = match.replace(/\[\^(\d+)\]:\s*(.*)/, '<li id="fn$1">$2 <a href="#ref$1" class="text-xs">↩</a></li>');
    return `<ol class="list-decimal ml-4 mb-1">${footnote}</ol>`;
  }).join('');

  // Handle paragraphs
  text = text.replace(/(?:\r?\n){2,}/g, '</p><p>').replace(/<\/p>\n<p>/g, '</p>\n<p>');
  text = '<p>' + text + '</p>';

  return DOMPurify.sanitize(text, { ADD_ATTR: ['target'] });
};
