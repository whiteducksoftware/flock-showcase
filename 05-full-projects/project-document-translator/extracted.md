|SAP Joule|Col2|Col3|
|---|---|---|
|Thema<br>SAP Joule, SAP Business AI|Version<br>1.0|Erstellt am<br>20.02.20235|
|Dokumentart<br>Overview|Autor<br>Katharina Spies|Geändert am<br>28.08.2025|

## **Executive Summary**

SAP Joule is SAP’s enterprise-focused generative AI copilot and agent system embedded across its cloud and
hybrid applications. It delivers productivity enhancements through natural language understanding, contextual
automation, and AI-driven insights by leveraging SAP’s Business Technology Platform (BTP), Knowledge
Graph, and Business Data Cloud. Systems are fully supported in S/4HANA Cloud (Public & Private), while OnPremise setups require a hybrid BTP-based configuration; classic ECC alone is unsupported. Interaction patterns include navigational, transactional/interactional, and informational/analytical, all accessible depending on
product and licensing. Licensing and pricing involve a base package often included, with premium and agentic
scenarios using AI Units. Costs scale with usage, necessitating careful estimation of usage volumes for budgeting, as high-end capabilities can be expensive.

## **Content**


Executive Summary ....................................................................................................................................... 1


Content .......................................................................................................................................................... 1


1 Introduction to SAP Joule .......................................................................................................................... 2


1.1 Copilot Capabilities ............................................................................................................................. 2


1.1.1 Key Features ............................................................................................................................ 2


1.1.2 Interaction Patterns ................................................................................................................... 2


1.2 Joule Agents ...................................................................................................................................... 2


1.3 Extensibility: Joule Studio ................................................................................................................... 2


2 System Requirements ............................................................................................................................... 3


3 Licensing and Cost .................................................................................................................................... 3


3.1 Joule products .................................................................................................................................... 3


4 Roadmap (2023 – 2026) ............................................................................................................................ 4


5 Strategic Benefits ...................................................................................................................................... 4


6 Governance and Security .......................................................................................................................... 4


7 Further information .................................................................................................................................... 5


7.1 Graphics ............................................................................................................................................. 5


7.2 Sources .............................................................................................................................................. 5


7.2.1 General Information .................................................................................................................. 5


7.2.2 Costs and Billing ....................................................................................................................... 6


1


|SAP Joule|Col2|Col3|
|---|---|---|
|Thema<br>SAP Joule, SAP Business AI|Version<br>1.0|Erstellt am<br>20.02.20235|
|Dokumentart<br>Overview|Autor<br>Katharina Spies|Geändert am<br>28.08.2025|

## **1 Introduction to SAP Joule**

SAP Joule is a generative AI-powered business copilot and autonomous agent platform embedded into SAP’s
cloud applications like S/4HANA Cloud, SuccessFactors, Ariba, Analytics Cloud, and more. It understands
business contexts, roles, and workflows to assist users with natural language commands facilitating navigation,
data retrieval, task automation, and analytics.

### **1.1 Copilot Capabilities**


**1.1.1 Key Features**


  Natural Language Querying and Commands across SAP modules including SAP Fiori, SuccessFactors, SAP Ariba, and SAP Analytics Cloud.


  Integration with Microsoft 365 Copilot for bi-directional task execution; this integration is rolling out
with general availability planned by Q3 2025.


  Real-time analytics and visualization capabilities directly integrated into workflows.


  Context-aware help through SAP’s Business Data Cloud and Knowledge Graph.


**1.1.2 Interaction Patterns**

|Pattern|Functionality|Example|
|---|---|---|
|Navigational|Guide users to apps/screens|“Open supplier invoices”|
|Transactional|Execute business actions in chat|“Create a purchase order for vendor X”|
|Informational|Retrieve structured business data|“Show top 5 open purchase requests”|
|Analytical|Explain or compare metrics|“Why did revenue fall last quarter?”|


### **1.2 Joule Agents**


Joule AI Agents are autonomous, multi-step AI workflows that perform complex business processes using over
a thousand AI "skills" (exact figures are internal estimates). They leverage SAP Knowledge Graph and Business Data Cloud to ground decisions and actions. Key examples include:


  **Cash-Collection Agent:** Automates overdue invoice resolution by coordinating finance, sales, and
support teams.


  **Sales Agent:** Generates account plans and quotations from customer communications.


  - **HR Agent:** Facilitates recruitment by suggesting job matches and managing onboarding flows.


Multiple agents can coordinate with each other and with human users to address broader business challenges
and cross-functional workflows. The library of agents is continuously expanding with new scenarios in procurement, supply chain, and field service management slated through 2025 and beyond.

### **1.3 Extensibility: Joule Studio**


Joule Studio, part of SAP Build, supports no-code/low-code development to create custom AI skills and agents.
It enables organizations to build tailored agents (e.g., specific for internal workflows), connect to external APIs,
and to use SAP BTP for deployment and governance.


2


|SAP Joule|Col2|Col3|
|---|---|---|
|Thema<br>SAP Joule, SAP Business AI|Version<br>1.0|Erstellt am<br>20.02.20235|
|Dokumentart<br>Overview|Autor<br>Katharina Spies|Geändert am<br>28.08.2025|


Planned general availability:


  - **Skill Builder:** Q3 2025


  - **Agent Builder:** Q4 2025


  - **Usage metrics dashboard** (to help monitor and optimize AI adoption): Q3 2025.

## **2 System Requirements**

|SAP Product|Joule Support|Notes|
|---|---|---|
|S/4HANA Cloud – Public|Fully supported natively|Deep integration, extensive AI capabilities|
|S/4HANA Cloud – Private (RISE)|/ Supported via SAP BTP|Requires BTP, Identity Authentication (IAS),<br>Cloud Connector|
|S/4HANA On-Premise|/ Limited support|Hybrid setup with BTP required; no native inte-<br>gration|
|ECC|Not supported|Upgrade or hybrid extension needed|



Technical prerequisites include SAP BTP, SAP Build Work Zone, Cloud Connector for hybrid environments,
and stable internet connectivity for AI model operations.

## **3 Licensing and Cost**


SAP uses AI Units as a virtual currency to consume Joule AI capabilities across cloud products. Each AI feature

‑
consumes units based on pre defined conversion metrics (e.g. per message, transaction, page view). One AI
Unit is currently priced at 7 euros. AI Units are contractually annual .


Embedded AI capabilities are unlocked via SAP AI Units while Joule is accessed through product licensing,
providing a base allocation of Joule messages annually for various cloud products. For instance, RISE with
S/4HANA Cloud Private Edition (base/premium) includes approximately 2,500 messages per year. Additional
usage is charged at around 7 AI Units for every 10,000 extra messages.

### **3.1 Joule products**


  - **Joule Base:** Included at no additional cost with eligible SAP cloud subscriptions. Offers unlimited usage for basic navigational, informational and transactional patterns **.**

  - **Joule Premium:** Paid add ‑ on (via AI Units) enabling domain ‑ specific, agentic and advanced capabilities (e.g. finance insights, procurement optimizations, agent workflows). Available for areas like financial management, spend management, developer tooling, SCM, HCM

  - **Joule for Developers**


3


|SAP Joule|Col2|Col3|
|---|---|---|
|Thema<br>SAP Joule, SAP Business AI|Version<br>1.0|Erstellt am<br>20.02.20235|
|Dokumentart<br>Overview|Autor<br>Katharina Spies|Geändert am<br>28.08.2025|

## **4 Roadmap (2023 – 2026)**

|Date|Milestone|
|---|---|
|Q4 2023|Joule embedded in SuccessFactors, SAP Start|
|Q1 2024|Joule launched in S/4HANA Public Cloud ERP|
|Q1 2025|First AI agents (e.g., cash collection) go live|
|Q2 2025|Microsoft 365 Copilot integration begins; Joule gains streaming response support|
|Q3 2025|WalkMe-powered action bar, context-aware search, Joule Studio Skill Builder, expanded domain integration<br>(Ariba, Fieldglass, Signavio)|
|Q4 2025|Custom Agent Builder GA, full Microsoft Copilot synergy, mobile app integrations (SuccessFactors Mobile,<br>Sales Cloud)|
|2026|Expanded AI agent library and broader SAP Business Suite integration|


## **5 Strategic Benefits**

Organizations can benefit from an increase in productivity through automated insights and proactive support
across functions. The unified AI interface facilitates cross-functional access and collaboration, breaking down
silos. Additionally, it ensures a consistent user experience across applications and devices, supporting interactions in natural language on web, desktop, and mobile platforms. Benefits across different functions:


  - **Finance:** Accelerated cash flow prediction, dispute resolution, and invoice management.


  **Supply Chain:** Predictive sourcing, inventory forecasting, and contract optimization.


  - **Sales/Service:** Intelligent contract analysis, deal insights, and faster ticket resolutions.


  - **HR:** Automated candidate matching, onboarding workflows, and workforce planning.


  **IT/Developers:** AI-assisted code generation, debugging, documentation, and workflow automation
within SAP Build and ABAP environments.

## **6 Governance and Security**


SAP Joule follows enterprise-grade security and responsible AI guidelines, including:


  - Human-in-the-loop validation to ensure oversight.


  - Explainable AI outputs enhancing algorithmic transparency.


  Model-agnostic frameworks supporting multiple AI providers (OpenAI, Google, Meta, etc.).


  Confidence scoring to gauge output reliability.


  Extensive logging and audit trails for compliance.


  - Role-based access controls and data isolation protect tenant security.


4


|SAP Joule|Col2|Col3|
|---|---|---|
|Thema<br>SAP Joule, SAP Business AI|Version<br>1.0|Erstellt am<br>20.02.20235|
|Dokumentart<br>Overview|Autor<br>Katharina Spies|Geändert am<br>28.08.2025|

## **7 Further information**

### **7.1 Graphics**

Figure 1: SAP Business AI (Source: SAP Business AI Approach White Paper)


Figure 2: Examples of Joule Interaction Patterns (Source: SAP Business AI White Paper)

### **7.2 Sources**


**7.2.1 General Information**


[https://www.sap.com/documents/2023/09/bac24f28-a57e-0010-bca6-c68f7e60039b.html](https://www.sap.com/documents/2023/09/bac24f28-a57e-0010-bca6-c68f7e60039b.html)



5


|SAP Joule|Col2|Col3|
|---|---|---|
|Thema<br>SAP Joule, SAP Business AI|Version<br>1.0|Erstellt am<br>20.02.20235|
|Dokumentart<br>Overview|Autor<br>Katharina Spies|Geändert am<br>28.08.2025|


**7.2.2 Costs and Billing**


[https://learning.sap.com/courses/positioning-sap-business-ai/understanding-pricing-and-commercial-aspects-](https://learning.sap.com/courses/positioning-sap-business-ai/understanding-pricing-and-commercial-aspects-3?utm_source=chatgpt.com)
[3?utm_source=chatgpt.com](https://learning.sap.com/courses/positioning-sap-business-ai/understanding-pricing-and-commercial-aspects-3?utm_source=chatgpt.com)


[https://community.sap.com/t5/technology-blog-posts-by-sap/sap-business-ai-what-does-it-cost/ba-](https://community.sap.com/t5/technology-blog-posts-by-sap/sap-business-ai-what-does-it-cost/ba-p/13960940)
[p/13960940](https://community.sap.com/t5/technology-blog-posts-by-sap/sap-business-ai-what-does-it-cost/ba-p/13960940)


                          [https://www.sap.com/products/artificial](https://www.sap.com/products/artificial-intelligence/pricing.html) intelligence/pricing.html


[https://discovery-center.cloud.sap/ai-feature/7062122c-d0be-4691-940b-1f3c275617f6/](https://discovery-center.cloud.sap/ai-feature/7062122c-d0be-4691-940b-1f3c275617f6/)


6


