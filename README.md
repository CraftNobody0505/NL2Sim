# NL2Sim: Natural Language to Simulink Model Generator
***A Framework for Automated Simulink Model Generation from Natural Language Specifications.***
<br>
***一个用于从自然语言规格说明自动生成Simulink模型的框架。***

![GitHub stars](https://img.shields.io/github/stars/CraftNobody0505/NL2Sim?style=social)
![GitHub forks](https://img.shields.io/github/forks/CraftNobody0505/NL2Sim?style=social)
![GitHub license](https://img.shields.io/github/license/CraftNobody0505/NL2Sim)

---

## 🌟 Overview | 项目总览

NL2Sim is a groundbreaking framework that bridges the gap between high-level system requirements described in natural language and their formal implementation in MATLAB/Simulink. Powered by a Large Language Model (LLM) engine constrained within a robust engineering system, NL2Sim dramatically accelerates the Model-Based Design (MBD) workflow, reduces manual errors, and lowers the technical barrier for domain experts.

*NL2Sim 是一个开创性的框架，它弥合了用自然语言描述的高层系统需求与在MATLAB/Simulink中进行形式化实现之间的鸿沟。在一个稳健的工程系统内，由一个受约束的大型语言模型（LLM）引擎驱动，NL2Sim 极大地加速了基于模型的设计（MBD）工作流，减少了人为错误，并为领域专家降低了技术门槛。*

**This entire project, from concept to a robust prototype, was developed in just 3 days by a programming novice in collaboration with Gemini.**
<br>
**整个项目，从概念到一个健壮的原型，是由一位编程新手与Gemini合作，在短短3天内完成的。**

---

## 🚀 Key Features | 核心特性

* **Natural Language Interface**: Describe your system in plain English or Chinese.
    * *自然语言接口：用简单的英文或中文描述您的系统。*
* **Complex Model Generation**: Capable of generating models with linear/non-linear dynamics, logic gates, feedback loops, and multi-level integrations.
    * *复杂模型生成：能够生成包含线性/非线性动态、逻辑门、反馈回路和多级积分的模型。*
* **Extensible Knowledge Base**: Easily extendable to support new Simulink blocks by simply updating an external JSON knowledge base, without touching the core code.
    * *可扩展的知识库：通过简单地更新一个外部JSON知识库，即可轻松扩展以支持新的Simulink模块，而无需触及核心代码。*
* **Robust & Decoupled Architecture**: A three-tier architecture ensures maintainability and reliability.
    * *稳健的解耦架构：三层架构确保了可维护性和可靠性。*

---

## 🛠️ How It Works | 工作原理

The system employs a three-tier decoupled architecture:
*NL2Sim 采用三层解耦架构：*

1.  **Frontend & Controller (`main_controller_web.py`)**: A Flask-based web server that accepts user requests and manages asynchronous tasks.
    * *前端与控制器：一个基于Flask的Web服务器，用于接收用户请求和管理异步任务。*
2.  **Instruction Generation Engine (`prompts.py`)**: The "brain" of the system. It uses a sophisticated prompt engineering framework and a dynamic knowledge base (`simulink_blocks_kb.json`) to guide an LLM (Gemini) in translating natural language into a structured JSON instruction sequence.
    * *指令生成引擎：系统的“大脑”。它使用一个复杂的提示工程框架和一个动态知识库，来引导LLM（Gemini）将自然语言翻译成结构化的JSON指令序列。*
3.  **Model Synthesis Service (`simulink_service.py`)**: The "hands" of the system. A standalone Python service that communicates with a local MATLAB/Simulink instance via the MATLAB Engine API to execute the JSON instructions atomically.
    * *模型合成服务：系统的“双手”。一个独立的Python服务，通过MATLAB引擎API与本地的MATLAB/Simulink实例通信，以原子方式执行JSON指令。*

<img width="768" height="1677" alt="system_architecture" src="https://github.com/user-attachments/assets/85d35c12-995c-4a0d-93a9-896e498c7a71" />

---

## ⚡️ Getting Started | 快速开始

### Prerequisites | 环境要求

* Python 3.8+
* MATLAB & Simulink (e.g., R2024b or newer)
* MATLAB Engine API for Python
* A Google AI API Key

### Installation & Setup | 安装与设置

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/CraftNobody0505/NL2Sim.git](https://github.com/CraftNobody0505/NL2Sim.git)
    cd NL2Sim
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(You will need to create a `requirements.txt` file)*
3.  **Set up your API Key:**
    ```bash
    export GOOGLE_API_KEY="YOUR_API_KEY"
    ```
4.  **Run the services:**
    * In one terminal, start the Simulink service:
        ```bash
        python simulink_service.py
        ```
    * In another terminal, start the main controller:
        ```bash
        python main_controller_web.py
        ```
5.  Open your browser and go to `http://127.0.0.1:8080`.

---

## 🏆 Showcase | 案例展示

We have successfully validated the framework with three increasingly complex models:
*我们已通过三个复杂度递增的模型成功验证了该框架：*

1.  **PID Controller**: A standard linear control system.
3.  **Thermostat**: A non-linear system with logic gates and feedback loops.
4.  **Projectile Motion**: A dynamic system involving trigonometric functions and second-order integration.

<img width="940" height="729" alt="inverted_pendulum_control" src="https://github.com/user-attachments/assets/2c728d8a-9216-4f46-a116-f9952ff4abc6" />
<img width="565" height="511" alt="inverted_pendulum_control_Oscilloscope" src="https://github.com/user-attachments/assets/35b5ec2d-4f5f-42d2-89c2-41908c067bf6" />
<img width="969" height="746" alt="Thermostat_Control_System" src="https://github.com/user-attachments/assets/4734f646-4764-47f4-973a-e0cd7492c255" />
<img width="562" height="505" alt="Thermostat_Control_System_Oscilloscope" src="https://github.com/user-attachments/assets/c8c04a72-9f69-4d5b-9246-c83fafc293e9" />
<img width="968" height="746" alt="projectile_motion_model" src="https://github.com/user-attachments/assets/06a45332-fe75-464e-9aa6-cc7df55a8d27" />
<img width="560" height="507" alt="projectile_motion_model_Oscilloscope" src="https://github.com/user-attachments/assets/b18404fa-9316-4541-b95e-34bc1b3331d4" />


---

## 📄 License | 许可证

This project is licensed under the [YOUR_CHOSEN_LICENSE]. See the `LICENSE` file for details.
*本项目采用 [您选择的许可证] 授权。详情请见 `LICENSE` 文件。*
