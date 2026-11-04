
import time
import re
import numpy as np

from pypdf import PdfReader
from google import genai


# ==========================================
# GEMINI MODEL CONFIGURATION
# ==========================================

CHAT_MODEL = "gemini-3.5-flash"
EMBED_MODEL = "gemini-embedding-001"


class RAGEngine:

    def __init__(self, api_key):

        self.client = genai.Client(api_key=api_key)

        # Store uploaded documents separately for each user
        self.user_documents = {}

    # ==========================================
    # 1. GENERATE GEMINI RESPONSE WITH RETRIES
    # ==========================================

    def generate_with_retry(self, prompt, max_retries=3):

        print("Using Gemini model:", CHAT_MODEL)

        for attempt in range(max_retries):

            try:

                response = self.client.models.generate_content(
                    model=CHAT_MODEL,
                    contents=prompt
                )

                return response

            except Exception as error:

                error_message = str(error).upper()

                # Retry only temporary service errors
                if (
                    "503" not in error_message
                    and "UNAVAILABLE" not in error_message
                ):
                    raise

                # Stop after the final attempt
                if attempt == max_retries - 1:
                    raise

                delay = 2 ** (attempt + 1)

                print(
                    f"Gemini service is busy. "
                    f"Retrying in {delay} seconds..."
                )

                time.sleep(delay)

    # ==========================================
    # 2. SPLIT PDF TEXT INTO CHUNKS
    # ==========================================

    def split_text(self, text, chunk_size=1000, overlap=150):

        text = re.sub(r"\s+", " ", text).strip()

        chunks = []

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunks.append(text[start:end])

            start += chunk_size - overlap

        return chunks

    # ==========================================
    # 3. GENERATE TEXT EMBEDDINGS
    # ==========================================

    def get_embedding(self, text, task_type):

        response = self.client.models.embed_content(
            model=EMBED_MODEL,
            contents=text,
            config={
                "task_type": task_type
            }
        )

        return response.embeddings[0].values

    # ==========================================
    # 4. PROCESS UPLOADED PDF FILES
    # ==========================================

    def process_pdf(self, files, user_id):

        user_id = str(user_id)

        all_chunks = []

        for file in files:

            reader = PdfReader(file.stream)

            pdf_text = []

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:
                    pdf_text.append(page_text)

            full_text = "\n".join(pdf_text)

            if not full_text.strip():
                continue

            chunks = self.split_text(full_text)

            for chunk in chunks:

                all_chunks.append({
                    "text": chunk,
                    "source": file.filename
                })

        if not all_chunks:

            raise ValueError(
                "No readable text found in the uploaded PDFs."
            )

        embeddings = []

        for chunk in all_chunks:

            vector = self.get_embedding(
                chunk["text"],
                "RETRIEVAL_DOCUMENT"
            )

            embeddings.append(vector)

        self.user_documents[user_id] = {
            "chunks": all_chunks,
            "vectors": np.array(embeddings)
        }

        return {
            "message": "PDFs processed successfully!",
            "files": len(files),
            "chunks": len(all_chunks)
        }

    # ==========================================
    # 5. RETRIEVE RELEVANT PDF CHUNKS
    # ==========================================

    def retrieve(self, question, user_id, top_k=4):

        user_id = str(user_id)

        documents = self.user_documents.get(user_id)

        if not documents:
            return []

        question_vector = np.array(
            self.get_embedding(
                question,
                "RETRIEVAL_QUERY"
            )
        )

        vectors = documents["vectors"]

        question_norm = np.linalg.norm(question_vector)

        vector_norms = np.linalg.norm(vectors, axis=1)

        similarities = np.dot(
            vectors,
            question_vector
        ) / (
            vector_norms * question_norm + 1e-10
        )

        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [
            documents["chunks"][index]
            for index in top_indices
        ]

    # ==========================================
    # 6. ANSWER QUESTIONS USING PDF (RAG)
    # ==========================================

    def ask(
        self,
        question,
        user_id,
        level="Beginner",
        language="English",
        top_k=4
    ):

        relevant_chunks = self.retrieve(
            question,
            user_id,
            top_k
        )

        if not relevant_chunks:

            return {
                "answer": (
                    "I could not find relevant information "
                    "in your uploaded documents."
                ),
                "sources": []
            }

        context = "\n\n".join(
            chunk["text"]
            for chunk in relevant_chunks
        )

        prompt = f"""
You are ClearMind AI, an intelligent PDF assistant.

Answer the user's question using the provided document context.

Explanation level: {level}
Required language: {language}

Instructions:
- Use simple and natural language.
- Write clear, easy-to-understand paragraphs.
- Explain difficult concepts in beginner-friendly words.
- Include examples when helpful.
- Do not use asterisks, hashtags, or Markdown formatting.
- Do not invent information.
- If the answer is not available in the document context,
  clearly say that the document does not provide that information.

Document context:
{context}

User question:
{question}

Answer:
"""

        response = self.generate_with_retry(prompt)

        return {
            "answer": response.text or "No answer generated.",
            "sources": list(dict.fromkeys(
                chunk["source"]
                for chunk in relevant_chunks
            ))
        }

    # ==========================================
    # 7. NORMAL AI CHAT WITHOUT PDF
    # ==========================================

    def ask_general(
        self,
        question,
        level="Beginner",
        language="English"
    ):

        prompt = f"""
You are ClearMind AI, a helpful AI assistant.

Answer the user's question clearly and accurately.

Explanation level: {level}
Required language: {language}

Instructions:
- Explain difficult concepts in simple words.
- Use clear and natural paragraphs.
- Give real-life examples wherever helpful.
- Keep the answer easy to understand.
- Do not use asterisks, hashtags, or Markdown formatting.
- Do not invent facts.
- If you are uncertain, say so.

User question:
{question}

Answer:
"""

        response = self.generate_with_retry(prompt)

        return {
            "answer": response.text or "No answer generated.",
            "sources": []
        }
