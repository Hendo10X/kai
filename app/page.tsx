"use client"

import {
  GoogleGenerativeAI,
  HarmCategory,
  HarmBlockThreshold,
} from "@google/generative-ai";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

const apiKey = process.env.NEXT_PUBLIC_GEMINI_API_KEY;
if (!apiKey) {
  throw new Error("API key is not defined");
}
const genAI = new GoogleGenerativeAI(apiKey);

const model = genAI.getGenerativeModel({
  model: "gemini-2.0-flash",
});

const generationConfig = {
  temperature: 1,
  topP: 0.95,
  topK: 40,
  maxOutputTokens: 8192,
  responseMimeType: "text/plain",
};

export default function Home() {
  const [data, setData] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const runAI = async (prompt: string) => {
    try {
      setLoading(true);
      const chatSession = model.startChat({
        generationConfig,
        history: [],
      });

      const result = await chatSession.sendMessage(prompt);
      const responseText = result.response.text();
      setData(responseText);
    } catch (error) {
      console.error("Error generating response:", error);
      setData("Sorry, there was an error generating a response.");
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const prompt = (event.target as HTMLFormElement).prompt.value || "";
    runAI(prompt);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <h1 className="text-2xl font-bold text-center mb-4 font-mono font-bold">Kai</h1>
      <p className="w-full max-w-md text-md text-center mb-7 font-mono tracking-tighter">
        Kai is an AI assistant that can help you with alot random questions bugging you.
      </p>
      <form onSubmit={onSubmit} className="w-full max-w-md space-y-4 font-mono">
        <div>
          <input
            type="text"
            placeholder="Enter your prompt"
            name="prompt"
            id="prompt"
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <div>
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex justify-center py-2 px-8 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300"
            >
              {loading ? "Generating..." : "Submit"}
            </button>
          </div>
        </div>
      </form>

      {data && (
        <div className="mt-6 w-full max-w-xl p-4 border rounded-md bg-gray-50">
          <h2 className="text-md font-medium text-gray-900 mb-2 font-mono">Response:</h2>
          <div className="prose prose-sm max-w-none font-mono text-sm">
            <ReactMarkdown
              components={{
                h1: ({ node, ...props }) => <h1 className="text-xl font-bold mt-4 mb-2" {...props} />,
                h2: ({ node, ...props }) => <h2 className="text-lg font-bold mt-3 mb-2" {...props} />,
                h3: ({ node, ...props }) => <h3 className="text-md font-bold mt-2 mb-1" {...props} />,
                p: ({ node, ...props }) => <p className="mb-2" {...props} />,
                ul: ({ node, ...props }) => <ul className="list-disc pl-5 mb-2" {...props} />,
                ol: ({ node, ...props }) => <ol className="list-decimal pl-5 mb-2" {...props} />,
                li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                code: ({ node, ...props }) => <code className="bg-gray-100 p-1 rounded" {...props} />,
                pre: ({ node, ...props }) => <pre className="bg-gray-100 p-2 rounded overflow-x-auto my-2" {...props} />,
                blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2" {...props} />,
                a: ({ node, ...props }) => <a className="text-blue-600 hover:underline" {...props} />,
                img: ({ node, ...props }) => <img className="max-w-full h-auto my-2" {...props} />,
                table: ({ node, ...props }) => <table className="min-w-full border-collapse border border-gray-300 my-2" {...props} />,
                th: ({ node, ...props }) => <th className="border border-gray-300 px-2 py-1 bg-gray-100" {...props} />,
                td: ({ node, ...props }) => <td className="border border-gray-300 px-2 py-1" {...props} />,
              }}
            >
              {data}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}