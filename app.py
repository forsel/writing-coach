# Bring in deps
import streamlit as st 
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain 


# Initialization
debug = True
ccss = 'CCSS.ELA-LITERACY.W.4.9'
ccss_link = 'https://www.thecorestandards.org/ELA-Literacy/W/4/#CCSS.ELA-Literacy.W.4.9'
grade = '4'
qcmax=3

# App framework
st.title('Writing coach')
st.write('Welcome, I provide questions related to Common Core standard [' + ccss + '](' + ccss_link + ') and will evaluate your answers according to a rubric. Please find more information on this standard and the rubric used in the side bar.')

# State
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key=''
if "ccss_desc" not in st.session_state:
    st.session_state.ccss_desc=''
if "rubric" not in st.session_state:
    st.session_state.rubric=''
if "qc_rubric" not in st.session_state:
    st.session_state.qc_rubric=''
if 'topic' not in st.session_state:
    st.session_state.topic=''
if 'question' not in st.session_state:
    st.session_state.question=''
if 'answer' not in st.session_state:
    st.session_state.answer=''

st.sidebar.text_input('OpenAI API Key', type='password', key='openai_api_key')

if not st.session_state.openai_api_key.startswith('sk-'):
    st.sidebar.warning('Please provide a valid OpenAI API key to continue')
else:

    # LLMs
    llm1 = ChatOpenAI(model='gpt-4', temperature=0, openai_api_key=st.session_state.openai_api_key)
    llm2 = ChatOpenAI(model='gpt-4', temperature=0.7, openai_api_key=st.session_state.openai_api_key)

    # Define CCSS standard and rubric only once
    with st.sidebar:

        if st.session_state.ccss_desc == '':

            with st.spinner('Determining info...'):
                ccss_template = PromptTemplate(
                    input_variables = ['ccss'], 
                    template='Provide a description of Common Core standard {ccss}'
                )

                ccss_chain = LLMChain(llm=llm1, prompt=ccss_template, verbose=debug, output_key='ccss_desc')

                st.session_state.ccss_desc = ccss_chain.run(ccss)

        with st.expander('Common Core standard ' + ccss + ' description'): 
            st.info(st.session_state.ccss_desc)

        if st.session_state.rubric == '':

            with st.spinner('Determining rubric...'):
                rubric_template = PromptTemplate(
                    input_variables = ['ccss'], 
                    template='Provide a concise rubric to evaluate student\'s responses for Common Core standard {ccss} with a point-based system'
                )

                rubric_chain = LLMChain(llm=llm1, prompt=rubric_template, verbose=debug, output_key='rubric')

                st.session_state.rubric = rubric_chain.run(ccss)

        with st.expander('Common Core standard ' + ccss + ' rubric'): 
            st.info(st.session_state.rubric)

        if st.session_state.qc_rubric == '':
            st.session_state.qc_rubric='''Introduction Clarity (20 Points): The introduction should clearly define the topic and give a brief overview. It should be concise, yet informative enough to provide a basic understanding of the topic.

Context Relevance (20 Points): The context should be directly related to the topic and should provide a deeper understanding of the topic. It should be relevant to the question that follows.

Question Quality (20 Points): The question should be open-ended, allowing for a range of possible answers. It should be based on the information provided in the introduction and context.

Question Relevance (20 Points): The question should be directly related to the topic and should be based on the information provided in the introduction and context.

Independence from External Sources (20 Points): The question should not reference external sources. The answer to the question should be able to be formed based on the information provided in the introduction and context.

Each of the five categories will be scored on a scale of 0-20, with 0 being the lowest and 20 being the highest. The final score will be out of 100.
'''

        with st.expander('Quality control rubric'): 
            st.info(st.session_state.qc_rubric)


    if st.button(label='Reset'):
        #st.session_state.qc_rubric=''
        st.session_state.topic=''
        st.session_state.question=''
        st.session_state.answer=''


    # Allow the student to input a topic
    st.text_input('Provide a topic of interest', key='topic', placeholder='E.g. baseball')


    # Main run (generate question, allow answer and evaluate)
    if st.session_state.topic:

        if st.session_state.question == '':
            succeeded = False;
            for x in range(1, qcmax+1):
                with st.spinner('Generating question...'):
                    # Create open-ended question
                    teacher_template = PromptTemplate(
                        input_variables = ['ccss', 'topic', 'grade'], 
                        template='''You are a creator of open-ended questions for students to test Common Core standard {ccss} related to topic "{topic}". Provide the following:
Introduction
Context
Question

The introduction, context, and question should be self-contained. It should be possible to answer the question with only the information in the introduction and context, no additional external information should be needed. Do not reference external sources in the introduction and context. The difficulty level of the introduction, context, and question should match grade level {grade} of the student.'''
                    )

                    teacher_chain = LLMChain(llm=llm2, prompt=teacher_template, verbose=debug, output_key='question')
                    st.session_state.question = teacher_chain.run(ccss=ccss, topic=st.session_state.topic, grade=grade)
                with st.spinner('Checking question quality...'):
                    # Quality control check
                    qc_template = PromptTemplate(
                        input_variables = ['qc_rubric', 'question'], 
                        template='''You evaluate the quality of questions based on a given rubric.
Given the rubric:
{qc_rubric}
Given the question:
{question}
determine a total score of the given question. If the score is below 60, then end the output with the word 'qc failed', otherwise end the output with the word 'qc succeeded'.'''
                    )

                    qc_chain = LLMChain(llm=llm2, prompt=qc_template, verbose=debug, output_key='qc_score')
                    qc_score = qc_chain.run(qc_rubric=st.session_state.qc_rubric, question=st.session_state.question)
                if debug:
                    with st.expander('QC score ' + str(x)): 
                        st.info(qc_score)

                if 'qc succeeded' in qc_score.lower():
                    succeeded = True
                    break

                if debug:
                    with st.expander('QC failed question ' + str(x)): 
                        st.info(st.session_state.question)
            if not succeeded:
                st.warning('Could not generate high-quality question after ' + str(qcmax) + ' tries, failed quality check. Please reset and try again.')
                st.session_state.question = ''
        st.info(st.session_state.question) 



        # Allow student to enter an answer and include simulation button for testing purposes
        if debug:
            if st.button(label='Simulate student answer'):
                with st.spinner('Simulating answer...'):
                    student_template = PromptTemplate(
                        input_variables = ['grade', 'question'], 
                        template='''You are a student in grade {grade}. You received the following question. Please answer it.

        {question}'''
                    )
                    student_chain = LLMChain(llm=llm2, prompt=student_template, verbose=debug, output_key='answer')
                    st.session_state.answer = student_chain.run(grade=grade, question=st.session_state.question)

    
        st.text_area(label='Provide your answer', key='answer')


        if st.session_state.answer:
            with st.spinner('Evaluating...'):
                evaluator_template = PromptTemplate(
                    input_variables = ['grade', 'rubric', 'question', 'answer'], 
                    template='''You are someone who evaluates answers given by students in grade {grade} on open-ended questions using a given rubric.
Given the rubric:
{rubric}
Given the question:
{question}
Given the answer:
{answer}
provide an evaluation of the given answer including a total score based on the given rubric. Add "answer is wrong" if the total score is lower than half of the maximum score possible. Add "answer is right" otherwise. Also provide some feedback to the student on how he or she can improve the answer. Ensure that the evaluation and feedback provided are on the grade level of the student.'''
                )
                evaluator_chain = LLMChain(llm=llm2, prompt=evaluator_template, verbose=debug, output_key='evaluation')
                evaluation = evaluator_chain.run(grade=grade, rubric=st.session_state.rubric, question=st.session_state.question, answer=st.session_state.answer)
            if 'answer is right' in evaluation.lower():
                st.success(evaluation)
            else:
                st.error(evaluation)
