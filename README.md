# Learning-LangGraph

An intermediate-level, comprehensive LangGraph course, focusing on practical use cases. 

## Setup

**NOTE:** If your intention is to only work on Google Colab - at least for the first part of the course - you can skip the virtual environment creation and go straight to [setting up env variables](./README.md#setting-up-env-variables). 

Still, the creation of a local virtual environment will be needed later on.

### Python version

Make sure you're using Python version 3.11, 3.12, or 3.13.
```
python3 --version
```

### Clone repo
```
git clone https://github.com/MatteoFalcioni/Learning-LangGraph.git
$ cd Learning-LangGraph
```

### Create an environment and install dependencies

#### Mac/Linux/WSL with Anaconda (recommended)
```
$ conda create -n learning-langgraph python=3.11 -y
$ conda activate learning-langgraph
$ pip install -r requirements.txt
```

#### Mac/Linux/WSL (without Anaconda)
```
$ python3 -m venv lc-academy-env
$ source lc-academy-env/bin/activate
$ pip install -r requirements.txt
```

### Setting up env variables
Briefly going over how to set up environment variables. 

#### From shell
We can do it from shell (Mac/Linux/WSL):
```
$ export API_ENV_VAR="your-api-key-here"
```
#### From code

##### Google Colab 
In Google Colab, follow these steps:

1. Open your Google Colab notebook and click on the 🔑 Secrets tab in the left panel.
    ![colab keys](notebooks/images/colab_keys.png)
2. Create a new secret with the desired name - for example, `OPENAI_API_KEY`.
3. Copy and paste your API key into the `Value` input box of `OPENAI_API_KEY`.
4. Toggle the button on the left to allow all notebooks access to the secret. 

##### Jupyter Notebooks or Python files
If we are using a generic local notebook with Jupyter, or if we are working with `.py` files, I recommend writing a `.env` file at your project root. 

**This `.env` file must be added to your `.gitignore` file so that you do not accidentally commit your secrets to GitHub** 

The `.env` file must have a structure like this:
```bash
OPENAI_API_KEY=<your_key_here>
```

Then we can use the `load_dotenv()` function from the `dotenv` python package:

```python
from dotenv import load_dotenv()

load_dotenv()
```
This will automatically load the secrets into the environment. Now all stuff requiring the `OPENAI_API_KEY` (in our example) will work. 

Once loaded we can also directly access the keys as 
```python
import os

load_dotenv()
openai_api_key = os.environ['OPENAI_API_KEY']  # or os.getenv('OPENAI_API_KEY')
```

### Set OpenAI API key
* If you don't have an OpenAI API key, you can sign up [here](https://openai.com/index/openai-api/).
*  Set `OPENAI_API_KEY` in your environment 

### Sign up and Set LangSmith API
* Sign up for LangSmith [here](https://docs.langchain.com/langsmith/create-account-api-key#create-an-account-and-api-key), find out more about LangSmith and how to use it within your workflow [here](https://www.langchain.com/langsmith). 
*  Set `LANGSMITH_API_KEY`, `LANGSMITH_TRACING_V2="true"` `LANGSMITH_PROJECT="langchain-academy"`in your environment 
*  If you are on the EU instance also set `LANGSMITH_ENDPOINT`="https://eu.api.smith.langchain.com" as well.

### Set up Tavily API for web search (Optional, but will be useful later on)

* Tavily Search API is a search engine optimized for LLMs and RAG, aimed at efficient, 
quick, and persistent search results. 
* You can sign up for an API key [here](https://tavily.com/). 
It's easy to sign up and offers a very generous free tier. Some lessons will use Tavily. 

* Set `TAVILY_API_KEY` in your environment.
