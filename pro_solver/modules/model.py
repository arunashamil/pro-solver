from langchain_mistralai.chat_models import ChatMistralAI
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate

class PDEPPrompt():
  def __init__(self,
               system_prompt: str,
               user_prompt: str,
               context: bool
               ):
    self.system_prompt = system_prompt
    self.user_prompt = user_prompt
    self.context = context


  @property
  def template(self) -> ChatPromptTemplate:
        if self.context:
            prompt_template = [
                ("system", self.system_prompt),
                ("human", "Use the following context to guide your answer: {context}\n" + self.user_prompt[1])
            ]
        else:
            prompt_template = [
                self.system_prompt,
                self.user_prompt
            ]
        return ChatPromptTemplate.from_messages(prompt_template)
  
class LLMModel:
    def __init__(self, api_key: str, model_name: str = "mistral-small-latest", temperature: float = 0.5):
        self.model = ChatMistralAI(
            model=model_name,
            temperature=temperature,
            max_retries=2,
            api_key=api_key
        )

    def __call__(self, prompt_template, input_data: dict):
        llm_chain = prompt_template | self.model
        return llm_chain.invoke(input_data)

class PDEOutput(BaseModel):
    install: str = Field(..., description="Python code that installs all required libraries.")
    function: str = Field(..., description="Python code defining the solve_pde function with imports.")
    example: str = Field(..., description="Python code that creates example input and runs solve_pde().")

class ModelPipeline():
  def __init__(self,
               model,
               rag_prompt: str,
               rag_vars: dict,
               user_prompt: str,
               user_vars: dict,
               system_prompt: str,
               section_name: str
               ):
    self.llm = model
    self.rag_temp = ChatPromptTemplate.from_messages(rag_prompt)
    self.rag_vars = rag_vars
    self.system_prompt = system_prompt
    self.user_vars = user_vars
    self.user_prompt = user_prompt
    self.section_name = section_name

  def search_rag_res(self, db, num_res):
    message = self.rag_temp.format_messages(**self.rag_vars)
    results = db.query(
                      query_texts=[message[1].content],
                      n_results=num_res,
                      where={"section": self.section_name}
                      )
    return ' '.join(results['documents'][0])

  def generate_prompt(self):
    return PDEPPrompt(self.system_prompt, self.user_prompt, context = True).template

  def generate_response(self, db, num_res, rag_context = None):
    if not rag_context:
      rag_context = self.search_rag_res(db, num_res)
    else:
      pass
    full_request = {
              **self.user_vars,
              'context': rag_context
              }
    prompt_temp = self.generate_prompt()
    return self.llm(prompt_temp, full_request).content