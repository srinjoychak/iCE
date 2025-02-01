# iCE (intelligent Copilot Engine)
## Prerequisites

- Docker
- Docker Compose

## System Requirements
   iCE operates in both Online and Offline environments. For Offline environments a GPU system is preferred for optimal performance, however the application works with only CPU.
   For online models (eg: ChatGPT, Azure OpenAI) the system spec would be the following: 8 CPU - 8 GB RAM - 20 GB storage 
   For offline environments, minimum systems recommended without GPU - 8 CPU - 16 GB RAM - 20 GB storage

   iCE has been tested in offline environment with following system specification - 16 CPU - 64 GB Memory - 40 GB A100 vRAM

## Steps to setup iCE

1. **Clone the Repository:**

   git clone [https://wwwin-github.cisco.com/iCE/iCE_ScrumBot_Ollama](https://github.com/srinjoychak/iCE)
   ```bash
      cd iCE
   ```

2. **Update the .env File:** 

   Populate the .env file with the required parameters. 
   - Update the `MODE` to `OpenAI`, `AzureOpenAI`, or `Offline` based on the LLM to be used.

   - **If MODE is OpenAI:**
      - Update `OPENAI_API_KEY` with the API Key from OpenAI.
      - Update `OPENAI_MODEL` with the OpenAI Model to use.

   - **If MODE is AzureOpenAI:**
      - Update `AZURE_MODEL` with the Azure OpenAI Model to use.
      - Update `AZURE_ENDPOINT` with the Azure endpoint.
      - Update `API_VERSION` with the API version.
      - Update `AZURE_OPEN_AI_API_KEY` with the API Key.
      - **If API Key has to be generated programmatically:**
         - Update `API_KEY_URL` with the endpoint to generate the API Key.
         - Update `CLIENT_ID` and `CLIENT_SECRET` for accessing the endpoint to generate the API Key.
         - Update `APPKEY` that has to be passed along with the generated API Key as model args.

   - **If MODE is Offline:**
      - Update `OLLAMA_MODEL` with the Ollama model to use.  
        **Note:** llama3.3 is optimal for agents but requires higher system resources.

   - Update `DEVICE_TYPE` to `cpu`, `cuda`, or `mps` depending on the specifications of your system.
   - Update `EMBEDDING_MODEL_NAME` as per requirements and system specifications.(For Doc Search)     
     **Note:** The default value is set to all-MiniLM-L12-v2 for CPU compatibility.

3. **Install iCE:**

   Run the following script to install all required services:
   ```bash
   bash install_ice_app.sh
   ```

4. **Access iCE:**

   Open your browser and navigate to:
   ```
   http://<server_ip>:5006
   ```

5. **Uninstall iCE:**

   Run the following script to uninstall all services:
   ```bash
   bash uninstall_ice_app.sh
   ```
## Steps to use Doc Search

1. **Enable Doc Search**
   
   - Click on the `Doc Search` toggle button to activate document retrieval.
   
2. **Upload Documents**

   - Click on the `Manage Documents` toggle button to access the document upload section.

   - Click on the `Browse File` button or drag and drop files into the upload area.

   - Click `Upload` and verify that the documents appear in the 'Available Documents' dropdown.
   
3. **Ingest Documents**
   
   - Click on the `Ingest` button to process and index the uploaded documents.
   
4. **Search for Answers**

   - Enter a query in the search box.

   - Click `Submit` to retrieve relevant answers based on the uploaded documents.
