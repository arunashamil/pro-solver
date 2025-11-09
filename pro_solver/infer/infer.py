import fire
from config.infer.config import Darcy_2d_betta_01_dict
from config.prompt.config import correction_question, system_math_prompt, system_prompt
from pro_solver.modules.model import LLMModel, ModelPipeline, PDEOutput
from pro_solver.modules.code import code_check, code_save
from pro_solver.modules.collection import load_collection
from pro_solver.modules.text_process import safe_json_parse
from config.database.config import DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL
from config.infer.config import LLM_NAME

def main(api_key: str, question: str, output_solver_name: str):
    model = LLMModel(api_key = api_key, model_name = LLM_NAME)
    collection = load_collection(DB_DIR, COLLECTION_NAME)
    #------ EQUATION DATA --------
    input_var = Darcy_2d_betta_01_dict #ReacDiff_Nu05_Rho20_dict
    #-----------------------------


    #----- RAG ------
    math_context = ModelPipeline(model,
                                correction_question,
                                input_var,
                                correction_question,
                                input_var,
                                system_math_prompt,
                                COLLECTION_NAME
                                ).generate_response(collection, 5)
    #-----------------------------


    full_request = {
                **input_var,
                'context': math_context
                }


    name = output_solver_name

    while(True):
        code_text = ModelPipeline(model,
                                    question,
                                    input_var,
                                    question,
                                    input_var,
                                    system_prompt,
                                    "code"
                                    ).generate_response(collection, math_context, 5)
        #print(code_text)
        #with open('code.txt', 'w') as f:
            #f.write(code_text.content)
        #--------OUTPUT--------
        try:
            code_json = safe_json_parse(code_text)
        except:
            continue
        pde_output = PDEOutput(**code_json)
        #----------------------

        full_code = "\n\n".join([
            #pde_output.install,
            pde_output.function,
            pde_output.example
        ])

        #print(full_code)

        final_code = "\n\n".join([
            #pde_output.install,
            pde_output.function])

        if not code_check(full_code):
            code_save(final_code, name)
            break

if __name__ == "__main__":
    fire.Fire(main)