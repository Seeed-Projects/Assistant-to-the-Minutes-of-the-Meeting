from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.embeddings import resolve_embed_model
from llama_index.llms.ollama import Ollama
from flask import Flask, jsonify, request, render_template


class RAG:
    def __init__(self):
        self.ragapp = Flask(__name__)
        self.port=7774
        self.setup_routes()

        self.input_dir_doc = '/home/seeed/aa/raw_meeting_transcript'
        self.documents = self.read_directory(input_dir=self.input_dir_doc)

        Settings.embed_model = resolve_embed_model("local:BAAI/bge-small-en-v1.5")
        Settings.llm = Ollama(model="llama3", request_timeout=120.0)

        self.index = VectorStoreIndex.from_documents(self.documents)
        self.query_engine = self.index.as_query_engine()

    def setup_routes(self):
        @self.ragapp.route('/')
        def index():
            return render_template('chat.html')
    
        @self.ragapp.route('/api/update-doc')
        def update_doc():
            self.documents = self.read_directory(input_dir=self.input_dir_doc)
            self.index = VectorStoreIndex.from_documents(self.documents,)
            self.query_engine = self.index.as_query_engine()
            return jsonify({"message": "documents update!"})
        
        @self.ragapp.route('/api/rag-query')
        def rag_query():
            usr_prompt = request.args.get('prompt', 'Hello!')
            print(usr_prompt)
            response = self.query_engine.query(usr_prompt)
            print(response)
            return jsonify({"message": str(response)})
        
    def run(self):
        self.ragapp.run(port=self.port)
    
    def read_directory(self, input_dir):
        reader = SimpleDirectoryReader(input_dir=input_dir)
        documents = reader.load_data()
        print(f"Loaded {len(documents)} docs from {input_dir}")
        return documents
        

if __name__ == '__main__':
    re = RAG()
    re.run()
