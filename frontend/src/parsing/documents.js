export const MAX_FILE_BYTES = 10 * 1024 * 1024;

export function validateFile(file) {
  if (!file || !/\.(txt|docx|pdf)$/i.test(file.name)) throw new Error('Choose a TXT, DOCX or selectable-text PDF file. You can also paste your resume below.');
  if (file.size > MAX_FILE_BYTES) throw new Error('This file exceeds the 10 MB limit. Choose a smaller file or paste your resume below.');
  if (file.size === 0) throw new Error('This file is empty. Choose another file or paste your resume below.');
  const extension = file.name.split('.').pop().toLowerCase();
  const allowed = {txt: ['text/plain'], pdf: ['application/pdf'], docx: ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']};
  if (file.type && file.type !== 'application/octet-stream' && !allowed[extension].includes(file.type)) {
    throw new Error('The file type does not match its filename. Choose a supported file or paste the text below.');
  }
  return extension;
}

export async function parseResume(file) {
  const extension = validateFile(file);
  try {
    const arrayBuffer = await file.arrayBuffer();
    let text;
    if (extension === 'txt') {
      const bytes = new Uint8Array(arrayBuffer);
      const encoding = bytes[0] === 0xff && bytes[1] === 0xfe ? 'utf-16le' : bytes[0] === 0xfe && bytes[1] === 0xff ? 'utf-16be' : 'utf-8';
      text = new TextDecoder(encoding, {fatal: true}).decode(bytes);
    } else if (extension === 'docx') {
      const mammoth = await import('mammoth/mammoth.browser.js');
      const result = await (mammoth.default ?? mammoth).extractRawText({arrayBuffer});
      text = result.value;
    } else {
      const pdfjs = await import('pdfjs-dist');
      const {default: workerUrl} = await import('pdfjs-dist/build/pdf.worker.min.mjs?url');
      pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;
      const task = pdfjs.getDocument({data: new Uint8Array(arrayBuffer), isEvalSupported: false, useWorkerFetch: false});
      let document;
      try {
        document = await task.promise;
        const pages = [];
        for (let index = 1; index <= document.numPages; index++) {
          const page = await document.getPage(index);
          const content = await page.getTextContent();
          pages.push(content.items.filter(item => typeof item.str === 'string').map(item => item.str + (item.hasEOL ? '\n' : ' ')).join('').trim());
          page.cleanup();
        }
        text = pages.join('\n\n');
      } finally {
        await task.destroy();
      }
    }
    if (!text?.trim()) {
      throw new Error(extension === 'pdf' ? 'No selectable text was found. Scanned PDFs need OCR. Paste the resume text below or choose a text-based document.' : 'No readable text was found. Choose another file or paste your resume below.');
    }
    return text.trim();
  } catch (error) {
    if (error.name === 'PasswordException') throw new Error('This PDF is password-protected. Use an unlocked copy or paste your resume below.');
    if (/paste|OCR/.test(error.message)) throw error;
    throw new Error(`We could not read this ${extension.toUpperCase()} file. It may be damaged or use an unsupported encoding. Choose another file or paste your resume below.`);
  }
}
