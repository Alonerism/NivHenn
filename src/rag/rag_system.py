import os
import json
from typing import List, Dict, Any, Optional
import openai
from dotenv import load_dotenv
import chromadb
import hashlib

# Load environment variables
load_dotenv()

class RAGSystem:
    def __init__(self, db_connection, collection_name: str = "insurance_policies"):
        """
        Initialize RAG system for insurance policy Q&A
        
        Args:
            db_connection: Database connection object
            collection_name: Name for the ChromaDB collection
        """
        self.db = db_connection
        self.collection_name = collection_name
        self.chroma_available = False
        self.collection = None
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Warning: OPENAI_API_KEY not found. RAG functionality will be limited.")
            self.openai_client = None
        else:
            self.openai_client = openai.OpenAI(api_key=api_key)
        
        # Initialize ChromaDB for local vector storage
        try:
            # Try newer ChromaDB initialization
            self.chroma_client = chromadb.PersistentClient(
                path="data/chroma_db"
            )
            self.chroma_available = True
        except Exception as e:
            print(f"Warning: Failed to initialize ChromaDB with newer method: {e}")
            try:
                # Fallback to older method
                self.chroma_client = chromadb.PersistentClient(
                    path="data/chroma_db"
                )
                self.chroma_available = True
            except Exception as e2:
                print(f"Warning: ChromaDB initialization failed: {e2}")
                print("RAG system will operate in fallback mode without vector search")
                self.chroma_client = None
                self.chroma_available = False
        
        # Get or create collection if ChromaDB is available
        if self.chroma_available:
            try:
                self.collection = self.chroma_client.get_collection(name=collection_name)
            except:
                try:
                    self.collection = self.chroma_client.create_collection(
                        name=collection_name,
                        metadata={"description": "Insurance policy documents for RAG"}
                    )
                except Exception as e:
                    print(f"Warning: Failed to create collection: {e}")
                    try:
                        # Create a minimal collection
                        self.collection = self.chroma_client.create_collection(
                            name=collection_name
                        )
                    except Exception as e2:
                        print(f"Error: Collection creation failed: {e2}")
                        self.chroma_available = False
                        self.collection = None
        
        # Initialize the knowledge base only if ChromaDB is available
        if self.chroma_available:
            self._initialize_knowledge_base()
        else:
            print("ChromaDB not available - knowledge base initialization skipped")
    
    def _initialize_knowledge_base(self):
        """Initialize the knowledge base with existing policy texts"""
        policy_texts = self.db.get_policy_texts()
        
        if not policy_texts:
            print("No policy texts found in database. Knowledge base will be empty.")
            return
        
        # Check if collection already has documents
        if self.collection.count() > 0:
            print(f"Knowledge base already initialized with {self.collection.count()} documents")
            return
        
        print(f"Initializing knowledge base with {len(policy_texts)} policy texts...")
        
        # Process and add policy texts to vector database
        documents = []
        metadatas = []
        ids = []
        
        for policy_text in policy_texts:
            # Split text into chunks for better retrieval
            chunks = self._split_text_into_chunks(policy_text['extracted_text'])
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{policy_text['id']}_{i}"
                
                documents.append(chunk)
                metadatas.append({
                    'policy_id': policy_text['policy_id'],
                    'policy_number': policy_text['policy_number'],
                    'building_code': policy_text['building_code'],
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })
                ids.append(chunk_id)
        
        # Add documents to collection
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Added {len(documents)} text chunks to knowledge base")
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks for better retrieval"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def add_policy_to_knowledge_base(self, policy_id: int, extracted_text: str, 
                                   policy_number: str, building_code: str):
        """Add a new policy to the knowledge base"""
        if not self.chroma_available:
            print(f"Warning: Cannot add policy {policy_number} to knowledge base - ChromaDB not available")
            return False
        
        chunks = self._split_text_into_chunks(extracted_text)
        
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{policy_id}_{i}"
            
            documents.append(chunk)
            metadatas.append({
                'policy_id': policy_id,
                'policy_number': policy_number,
                'building_code': building_code,
                'chunk_index': i,
                'total_chunks': len(chunks)
            })
            ids.append(chunk_id)
        
        # Add to collection
        if documents:
            try:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"Added policy {policy_number} to knowledge base ({len(chunks)} chunks)")
                return True
            except Exception as e:
                print(f"Error adding policy to knowledge base: {e}")
                return False
        
        return False
    
    def query_policies(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Query the knowledge base and generate an answer using OpenAI
        
        Args:
            question: Natural language question about policies
            top_k: Number of relevant chunks to retrieve
            
        Returns:
            Dictionary containing answer and source information
        """
        # Check if RAG system is fully available
        if not self.chroma_available:
            return {
                'answer': "I'm sorry, but the knowledge base is not currently available. Please check that ChromaDB is properly installed and configured.",
                'sources': [],
                'confidence': 0.0,
                'error': 'ChromaDB not available'
            }
        
        if not self.openai_client:
            return {
                'answer': "I'm sorry, but the OpenAI API is not configured. Please set your OPENAI_API_KEY in the .env file.",
                'sources': [],
                'confidence': 0.0,
                'error': 'OpenAI not configured'
            }
        
        try:
            # Search for relevant policy chunks
            results = self.collection.query(
                query_texts=[question],
                n_results=top_k
            )
            
            if not results['documents'] or not results['documents'][0]:
                return {
                    'answer': "I couldn't find any relevant information in the policy documents to answer your question.",
                    'sources': [],
                    'confidence': 0.0
                }
            
            # Prepare context from retrieved chunks
            context_chunks = results['documents'][0]
            source_metadata = results['metadatas'][0]
            source_distances = results['distances'][0]
            
            # Create context string
            context = "\n\n".join([
                f"Document {i+1} (Policy: {meta['policy_number']}, Building: {meta['building_code']}):\n{chunk}"
                for i, (chunk, meta) in enumerate(zip(context_chunks, source_metadata))
            ])
            
            # Generate answer using OpenAI
            answer = self._generate_answer_with_openai(question, context)
            
            # Prepare source information
            sources = []
            for i, (meta, distance) in enumerate(zip(source_metadata, source_distances)):
                sources.append({
                    'policy_number': meta['policy_number'],
                    'building_code': meta['building_code'],
                    'chunk_index': meta['chunk_index'],
                    'relevance_score': 1.0 - distance,  # Convert distance to similarity score
                    'text_preview': context_chunks[i][:200] + "..." if len(context_chunks[i]) > 200 else context_chunks[i]
                })
            
            # Calculate overall confidence
            avg_relevance = sum(source['relevance_score'] for source in sources) / len(sources)
            
            return {
                'answer': answer,
                'sources': sources,
                'confidence': avg_relevance,
                'context_used': context[:1000] + "..." if len(context) > 1000 else context
            }
            
        except Exception as e:
            print(f"Error in RAG query: {e}")
            return {
                'answer': f"An error occurred while processing your question: {str(e)}",
                'sources': [],
                'confidence': 0.0
            }
    
    def _generate_answer_with_openai(self, question: str, context: str) -> str:
        """Generate answer using OpenAI API with retrieved context"""
        try:
            system_prompt = """You are an insurance policy expert assistant. You help users understand insurance policies by answering questions based on the provided policy documents.

IMPORTANT RULES:
1. Only answer based on the information provided in the context
2. If the context doesn't contain enough information, say so clearly
3. Be specific and cite policy numbers and building codes when relevant
4. Use clear, professional language
5. If comparing policies, highlight key differences
6. Always cite your sources from the context

Context from policy documents:
{context}

User Question: {question}

Please provide a comprehensive answer based on the context above."""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt.format(context=context, question=question)},
                    {"role": "user", "content": question}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"I encountered an error while generating the answer: {str(e)}"
    
    def compare_policies(self, policy_ids: List[int]) -> Dict[str, Any]:
        """Compare multiple policies and highlight differences"""
        if len(policy_ids) < 2:
            return {'error': 'Need at least 2 policies to compare'}
        
        # Get policy information
        policies = []
        for policy_id in policy_ids:
            policy_texts = self.db.get_policy_texts()
            policy_text = next((pt for pt in policy_texts if pt['policy_id'] == policy_id), None)
            if policy_text:
                policies.append(policy_text)
        
        if len(policies) < 2:
            return {'error': 'Could not retrieve enough policies for comparison'}
        
        # Create comparison prompt
        comparison_prompt = f"""Please compare the following {len(policies)} insurance policies and highlight the key differences in coverage, limits, deductibles, and other important terms.

Policies to compare:
{chr(10).join([f"Policy {i+1}: {p['policy_number']} (Building: {p['building_code']})" for i, p in enumerate(policies)])}

Please provide a detailed comparison focusing on:
1. Coverage types and limits
2. Deductibles
3. Premiums
4. Endorsements or riders
5. Exclusions
6. Any other significant differences

Use the policy information from the knowledge base to provide accurate comparisons."""

        # Query the system
        return self.query_policies(comparison_prompt, top_k=10)
    
    def search_policies(self, search_term: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for policies containing specific terms"""
        if not self.chroma_available:
            print("Warning: Policy search not available - ChromaDB not available")
            return []
        
        try:
            results = self.collection.query(
                query_texts=[search_term],
                n_results=top_k
            )
            
            if not results['documents'] or not results['documents'][0]:
                return []
            
            # Group results by policy
            policy_results = {}
            for i, (chunk, meta, distance) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0], 
                results['distances'][0]
            )):
                policy_id = meta['policy_id']
                if policy_id not in policy_results:
                    policy_results[policy_id] = {
                        'policy_number': meta['policy_number'],
                        'building_code': meta['building_code'],
                        'relevance_score': 1.0 - distance,
                        'matching_chunks': []
                    }
                
                policy_results[policy_id]['matching_chunks'].append({
                    'chunk_index': meta['chunk_index'],
                    'text_preview': chunk[:200] + "..." if len(chunk) > 200 else chunk,
                    'relevance': 1.0 - distance
                })
            
            # Convert to list and sort by relevance
            results_list = list(policy_results.values())
            results_list.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return results_list
            
        except Exception as e:
            print(f"Error in policy search: {e}")
            return []
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        if not self.chroma_available:
            return {
                'total_documents': 0,
                'unique_policies': 0,
                'collection_name': self.collection_name,
                'status': 'unavailable',
                'error': 'ChromaDB not available'
            }
        
        try:
            total_documents = self.collection.count()
            
            # Get unique policies
            if total_documents > 0:
                all_docs = self.collection.get()
                unique_policies = set()
                for meta in all_docs['metadatas']:
                    unique_policies.add(meta['policy_number'])
                
                return {
                    'total_documents': total_documents,
                    'unique_policies': len(unique_policies),
                    'collection_name': self.collection_name,
                    'status': 'active'
                }
            else:
                return {
                    'total_documents': 0,
                    'unique_policies': 0,
                    'collection_name': self.collection_name,
                    'status': 'empty'
                }
                
        except Exception as e:
            return {
                'error': str(e),
                'status': 'error'
            }
