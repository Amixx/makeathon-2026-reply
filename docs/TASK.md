## **REPLY Challenge: The Campus Co-Pilot Suite**

**Being a student at TUM should be about learning and growingâ€”not managing a logistical nightmare.**

Today's student experience is fragmented across an endless maze of disconnected platforms: **TUMonline** for exams and courses, **Moodle** for slides, the **Library portal** for study spaces, and **ZHS** for sports exactly when registration opens. Add in **Mensa** menus, **GitLab**, **Confluence/WIKI**, and chats across **Matrix, Zulip**, and **WhatsApp**, and navigating campus life becomes a chaotic bureaucratic struggle.

**What if navigating university logistics was as simple as having your own autonomous chief of staff?**

*â€œFind me an empty study room near the math building today at 2 PM, summarize the new Moodle slides, and sign me up for the reply workshop on Tuesday.â€*

**Why the current situation is frustrating:**
Students are forced to act as human APIsâ€”manually scraping deadlines from half a dozen portals and syncing them across calendars. Systems donâ€™t talk to each other, resulting in missed deadlines, overlapping events, and massive administrative friction that steals time away from the actual university experience.

---

### **The Challenge**

Your task is to build **The Campus Co-Pilot Suite: Agents for Students by Students**. We challenge you to design an autonomous agent (or a multi-agent system) capable of interacting with the universityâ€™s diverse ecosystem to **perform concrete actions** like booking rooms, organizing study materials, and managing schedules. Additionally, the system should act as a proactive personal coachâ€”optimizing your professional appearance and scouting for growth opportunities. We want you to move beyond simple conversational chatbots to **build real, orchestrating agents that tackle actual logistical friction and actively guide student success**.

---

### **Your Mission**

Your mission is to build an autonomous AI agent (or multi-agent system) that fundamentally transforms an aspect of student life at TUM through self-directed action.

Because you are the true experts of the student experience, you know better than anyone where the biggest frustrations lie. To succeed, your team should follow a simple three-step approach:

1. **Identify the Pain Point**  
   Dive deep into your daily university life. Pinpoint a genuine logistical problem, administrative hurdle, or organizational barrier that you and your peers face, and ideate a high-impact use case to solve it.

2. **Architect the Agent**  
   Design and build an intelligent agent that proactively tackles the problem. Your system should bridge disconnected platforms, navigate bureaucracy autonomously, and perform concrete actions on the user's behalf.

3. **Demonstrate the Impact**  
   Show us the real-world value. Demonstrate how your solution creates a tangible, positive impact on studentsâ€™ livesâ€”whether it saves hours of time, eliminates stress, or unlocks new career and learning opportunities.

**To fuel your brainstorming, here are a few examples of what you *could* build (but remember, itâ€™s completely up to you to define the problem!):**

* **The Autonomous Study Buddy:** Input a complex lecture topic, and the system spawns three agentsâ€”a *Skeptic* to find counter-arguments, a *Simplifier* to explain it easily, and a *Researcher* for real-world case studiesâ€”who collaborate to build the ultimate study guide.
* **The Study Career Agent:** An agent that audits your professional hygiene. It scans your CV for red flags (e.g., *<gamer_king99@gmail.com>*), cross-references your transcript against modern tech stacks, and scouts perfectly matching working student jobs or Reply workshops.
* **The Extracurricular Scout:** Navigates portals like ZHS to secure highly competitive sports spots the exact second they open, or tracks student club meetings to seamlessly integrate them into gaps in your calendar.

---

### **What Youâ€™ll Have Access To**

#### We will provide a number of tools to you in order to build your agent

* **Development tools:** AWS SageMaker Notebooks, and AWS Bedrock for development tools supporting it (like OpenCode see [OpenCode via Bedrock](https://opencode.ai/docs/providers/#amazon-bedrock))
* **Cloud services:** One AWS account per team pre-configured. Check out the resources under Kickstar & Examples to learn more about AWS services!
* **AI Models via AWS Amazon Bedrock:**
  * **Anthropic Claude Sonnet/Opus 4.6** â€” text generation, reasoning, coding
  * **Amazon Nova Pro** â€” text generation, multimodal
  * **Amazon Titan Text Embeddings v2** â€” convert text to vectors for search/RAG
  * **Llama 4, DeepSeek R1 and many more.** Full list of available models: [Bedrock Inference Profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html)
* **Tum systems**: We compiled a quick list of TUM web pages and services which your agent could interact with [here](https://github.com/DataReply/makeathon/blob/main/tum_systems.md)
  
---

### **Kickstart & Examples**

To help you with getting started, weâ€™ve prepared some starter resources and examples. Check them out to accelerate your development:

* **AWS Kickstart Slides:** [https://github.com/DataReply/makeathon/blob/main/Makeathon%20AWS%20Quickstart%20Guide.pdf](https://github.com/DataReply/makeathon/blob/main/Makeathon%20AWS%20Quickstart%20Guide.pdf): These slides should help you to familiarize yoursselves with the different AWS services you might use
* **Example Repo:** [https://github.com/DataReply/makeathon](https://github.com/DataReply/makeathon)
  * We prepared some python (.py and notebook) examples files to demonstrate how to use some AWS services including s3 (general storage solution) and Bedrock (LLMs hosted by AWS) in code. Furthermore there is an example notebook showing you how to simply set up a vecor database from an html input file using s3vectors and how to create a Langgraph agent with access to this database as a tool [here](https://github.com/DataReply/makeathon/blob/main/python/notebooks/RAG_agent_example.ipynb).
  * Alternatively, if you are a Nodejs/Typescript fan, there's some examples in typescript as well [here](https://github.com/DataReply/makeathon/blob/main/typescript/README.md) where you can see how to access S3, invoke Bedrock models, build a RAG with S3 Vectors and create a Langchain pipeline with Bedrock.

---

### **What Weâ€™re Looking For**

We will evaluate your project based on the following criteria:

* **Innovation & Ambition:** Are you building something truly novel? We are looking for creative agent architecture and the ambition to tackle complex logistical or educational problems.
* **Integration Depth & Autonomy:** Does your agent simply retrieve text, or does it *act*? High scores go to projects that cleanly interact with platforms (TUMonline, Moodle, Library APIs, etc.) and perform actions autonomously.
* **Real-World Impact & Overall Quality:** Does it genuinely alleviate student friction? We value robust, well-engineered solutions that have a tangible, positive effect on actual university life.
* **User Interface & User Experience:** The magic of an agent lies in how seamlessly the user can interact with it. We are looking for an intuitive, frictionless experience.
* **Presentation Quality:** Can you effectively convey your chosen pain point, demonstrate your solution, and prove the impact your agent generates during your final pitch?

---

### **Why It Matters**

This challenge is about much more than surviving the next semester at TUM. Next to genuinly helping students think about the potential of similar tools outside of university life.

You are building software that gives agency back to individuals. Whether it's a university ecosystem, a massive corporation, or a complex government infrastructure, bureaucratic friction exists everywhere.

An autonomous agent capable of orchestrating actions across disconnected systems is the holy grail of modern AI enterprise software. Building this for TUM can genuinely boost student life, with the potential to be established as a real, permanent service at the university.

Provide a real impact, inspire others, and build something that lives on far beyond the hackathon!
