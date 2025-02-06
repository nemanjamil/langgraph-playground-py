import dotenv from 'dotenv';
dotenv.config();

import { TavilySearchResults } from "@langchain/community/tools/tavily_search";
import { ChatOpenAI } from "@langchain/openai";
import { HumanMessage, AIMessage } from "@langchain/core/messages";
import { ToolNode } from "@langchain/langgraph/prebuilt";
import { StateGraph, MessagesAnnotation } from "@langchain/langgraph";
import { BaseLanguageModelInput } from '@langchain/core/language_models/base';
import { DynamicTool } from "@langchain/core/tools";
import readline from "readline";

// Simulated database for storing chat history
const chatHistoryDB: { [key: string]: any[] } = {};

// Function to return history for a thread
function getHistory(threadId: string): any[] {
  return chatHistoryDB[threadId] || [];
}

// Function to save messages to history
function saveToHistory(threadId: string, message: any): void {
  if (!chatHistoryDB[threadId]) {
    chatHistoryDB[threadId] = [];
  }
  chatHistoryDB[threadId].push(message);
}

// Add initial messages to history with threadId 1
const initialMessages = [
  new HumanMessage(
    `Generate a json creative, engaging, and humanized social media marketing campaign with five unique posts for a new product launch.
     Product: Nirmata - AI-Powered Custom RAG Solution
     Strategy: cost-efficiency and scalability
     Company: Nirmata
     Target Audience: SaaS and PaaS providers, enterprise clients
     Unique Selling Points: Flexible deployment: Choose a low-cost monthly subscription or self-host on your VPS, AWS, or preferred cloud. Features AI marketing agent, AI assistants with scoped management, and seamless Jira & Confluence integration.
     Find the latest trends in this industry and tailor five distinct and compelling marketing posts, each addressing a key aspect of the campaign. Display the relevant trend alongside each post for debugging.
     Output Schema: { "posts": [{ "postNumber": number, "content": string, "associatedTrend": string }] }`
  )
];

chatHistoryDB["1"] = initialMessages;

const tools = [new TavilySearchResults({ maxResults: 5 })];

// Function to return marketing trends
async function get_trends() {
  return [
    "AI in Marketing",
    "Cost-Efficiency Solutions",
    "Scalability in SaaS",
    "Enterprise AI Integration",
    "Cloud Deployment Trends",
  ];
}

// Create a valid tool for trends
const trendsTool = new DynamicTool({
  name: "get_trends",
  description: "Fetches the latest marketing trends",
  func: async () => JSON.stringify(await get_trends()), // Convert result to string
});

// Create a ToolNode
const toolNode = new ToolNode([...tools, trendsTool]);

// Initialize model and bind tools
const model = new ChatOpenAI({ model: "gpt-4o", temperature: 0.8, apiKey: process.env.OPENAI_API_KEY })
  .bindTools([trendsTool, ...tools]);


interface MarketingPost {
  postNumber: number;
  content: string;
  associatedTrend?: string;
}

interface MarketingCampaign {
  product: string;
  strategy: string;
  company: string;
  audience: string;
  usp: string;
  posts: MarketingPost[];
}

interface Feedback {
  edit: boolean;
  changes?: { index: number; feedback: string }[];
}

function getUserInput(product: any, strategy: any, company: any, audience: any, usp: any) {
  console.log("Accepting user input");
  return new HumanMessage(
    `Generate a json creative, engaging, and humanized social media marketing campaign with five unique posts for a new product launch.
     Product: ${product}
     Strategy: ${strategy}
     Company: ${company}
     Target Audience: ${audience}
     Unique Selling Points: ${usp}
     Find the latest trends in this industry and tailor five distinct and compelling marketing posts, each addressing a key aspect of the campaign. Display the relevant trend alongside each post for debugging.
     Output Schema: { "posts": [{ "postNumber": number, "content": string, "associatedTrend": string }] }`
  );
}

function getUserFeedback(posts: MarketingPost[]): Promise<Feedback> {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    console.log("\nGenerated Marketing Posts:");
    posts.forEach((post, index) => console.log(`Post ${index + 1}: ${JSON.stringify(post, null, 2)}\n`));

    rl.question("Are you satisfied with these posts? (yes/no): ", (answer) => {
      if (answer.toLowerCase() === "yes") {
        rl.close();
        resolve({ edit: false });
      } else {
        console.log("Which post(s) need editing? (Provide comma-separated post numbers)");
        rl.question("> ", (postNumbers) => {
          const indices = postNumbers.split(",").map(num => parseInt(num.trim()) - 1);
          const changes: { index: number; feedback: string }[] = [];

          const askForChanges = (i: number) => {
            if (i >= indices.length) {
              rl.close();
              resolve({ edit: true, changes });
              return;
            }
            const index = indices[i];
            rl.question(`What changes do you want for Post ${index + 1}?\n> `, (feedback) => {
              changes.push({ index, feedback });
              askForChanges(i + 1);
            });
          };
          askForChanges(0);
        });
      }
    });
  });
}

function shouldContinue({ messages }: { messages: any[] }) {
  console.log("Determining if we need to fetch additional information");
  const lastMessage = messages[messages.length - 1];
  const decision = lastMessage.tool_calls?.length ? "tools" : "__end__";
  console.log(`Decision: ${decision}`);
  return decision;
}

async function callModel(state: { messages: BaseLanguageModelInput; }) {
  console.log("Calling the model");
  console.log("Messages received:", state.messages);
  const response = await model.invoke(state.messages);
  // saveToHistory("1", "AI" +response.content);
  console.log("Model response received");
  return { messages: [response] };
}

const workflow = new StateGraph(MessagesAnnotation)
  .addNode("agent", callModel)
  .addEdge("__start__", "agent")
  .addNode("tools", toolNode)
  .addEdge("tools", "agent")
  .addConditionalEdges("agent", shouldContinue);

const app = workflow.compile();

async function generateMarketingPosts(
  product: string,
  strategy: string,
  company: string,
  audience: string,
  usp: string,
  includeHistory: boolean,
  threadId: string
): Promise<MarketingCampaign> {
  console.log("Executing the workflow");

  try {
    let history = [];
    // saveToHistory("1", "User" + getUserInput(product, strategy, company, audience, usp).content);

    if (includeHistory) {
      history = getHistory(threadId);
    }

    // Get new user input message
    const userMessage = getUserInput(product, strategy, company, audience, usp);

    // Combine history with new user input
    const messages = [...history, userMessage];

    // Invoke the AI model with full context
    const initialState = await app.invoke({ messages });
    
    const rawContent = initialState.messages[initialState.messages.length - 1].content as string;

    console.log("Raw Content Received:", rawContent);

    // Extract JSON content using regex (if needed)
    const jsonMatch = rawContent.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("Failed to extract JSON from response.");
    }

    const parsedContent = JSON.parse(jsonMatch[0]);

    if (!Array.isArray(parsedContent.posts)) {
      throw new Error("Parsed content does not contain a valid 'posts' array.");
    }

    const posts: MarketingPost[] = parsedContent.posts.map((post: any, index: number) => ({
      postNumber: post.postNumber ?? index + 1, // Ensure a valid postNumber
      content: post.content ?? "No content available",
      associatedTrend: post.associatedTrend ?? "No trend provided",
    }));

    // Get user feedback on the generated posts
    const feedback = await getUserFeedback(posts);

    if (feedback.edit) {
      console.log("Regenerating based on feedback...");
      for (const change of feedback.changes || []) {
        console.log(`Editing Post ${change.index + 1}: ${change.feedback}`);
        posts[change.index].content = change.feedback;
      }
    } else {
      console.log("Posts finalized!");
    }

    return { product, strategy, company, audience, usp, posts };
  } catch (error) {
    console.error("Error generating marketing posts:", error);
    throw new Error("Failed to generate marketing posts due to JSON parsing issues.");
  }
}

(async () => {
  const product = "NA - Get data from history";
  const strategy = "NA";
  const company = "NA";
  const audience = "NA";
  const usp = "NA";
  const threadId = "1";
  console.log("Starting example usage");
  const marketingCampaign = await generateMarketingPosts(product, strategy, company, audience, usp, true, threadId);
  console.log("Generated Marketing Campaign:", JSON.stringify(marketingCampaign, null, 2));
})();
