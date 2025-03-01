"use client"

import {
  GoogleGenerativeAI,
  HarmCategory,
  HarmBlockThreshold,
} from "@google/generative-ai";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Copy, Check } from "lucide-react";

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
  const [copied, setCopied] = useState<boolean>(false);

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
    const formElement = event.target as HTMLFormElement;
    const prompt = formElement.prompt.value || "";
    if (prompt.trim()) {
      runAI(prompt);
      // Optional: Clear the input after submission
      formElement.reset();
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(data);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-gradient-to-b from-white to-gray-50">
      <div className="w-full max-w-2xl">
        <h1 className="text-3xl font-bold text-center mb-4 font-mono bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600">Kai</h1>
        <p className="w-full text-md text-center mb-7 font-mono tracking-tighter text-gray-700">
          Kai is a physics AI assistant that can help you with any questions.
        </p>
        
        <form onSubmit={onSubmit} className="space-y-4 font-mono">
          <div className="relative">
            <input
              type="text"
              placeholder="Ask me about anything..."
              name="prompt"
              id="prompt"
              className="block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200 text-gray-800"
              autoComplete="off"
            />
          </div>
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center justify-center py-2 px-8 border border-transparent rounded-md shadow-md text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-60 transition-all duration-200 transform hover:-translate-y-1"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating...
                </>
              ) : (
                "Ask Kai"
              )}
            </button>
          </div>
        </form>

        {data && (
          <div className="mt-8 border rounded-lg bg-white shadow-lg overflow-hidden transition-all duration-300 ease-in-out">
            <div className="flex justify-between items-center p-4 border-b">
              <h2 className="text-lg font-medium text-gray-800 font-mono">Response:</h2>
              <button
                onClick={copyToClipboard}
                className="p-2 text-gray-500 hover:text-indigo-600 rounded-full hover:bg-gray-100 transition duration-200"
                title="Copy to clipboard"
              >
                {copied ? <Check size={18} className="text-green-500" /> : <Copy size={18} />}
              </button>
            </div>
            
            <div className="max-h-96 overflow-y-auto p-5 scrollbar-custom">
              <div className="prose prose-sm text-sm max-w-none font-mono text-gray-700">
                <ReactMarkdown
                  components={{
                    h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mt-6 mb-4 text-gray-800" {...props} />,
                    h2: ({ node, ...props }) => <h2 className="text-xl font-bold mt-5 mb-3 text-gray-800" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-lg font-bold mt-4 mb-2 text-gray-800" {...props} />,
                    p: ({ node, ...props }) => <p className="mb-4 leading-relaxed" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc pl-6 mb-4 space-y-1" {...props} />,
                    ol: ({ node, ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-1" {...props} />,
                    li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                    code: ({ node, ...props }) => <code className="bg-gray-100 px-1 py-0.5 rounded-md" {...props} />,
                    blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-indigo-300 pl-4 italic my-4 text-gray-600" {...props} />,
                    a: ({ node, ...props }) => <a className="text-indigo-600 hover:underline transition duration-200" {...props} />,
                    img: ({ node, ...props }) => <img className="max-w-full h-auto my-4 rounded-md shadow-sm" {...props} />,
                    table: ({ node, ...props }) => <div className="overflow-x-auto my-4"><table className="min-w-full border-collapse border border-gray-300" {...props} /></div>,
                    th: ({ node, ...props }) => <th className="border border-gray-300 px-4 py-2 bg-gray-100 text-left" {...props} />,
                    td: ({ node, ...props }) => <td className="border border-gray-300 px-4 py-2" {...props} />,
                  }}
                >
                  {data}
                </ReactMarkdown>
              </div>
            </div>
            
            {data.length > 500 && (
              <div className="flex justify-center py-2 border-t bg-gradient-to-t from-white via-white to-transparent">
                <span className="text-xs text-gray-500 animate-bounce">Scroll for more</span>
              </div>
            )}
          </div>
        )}
      </div>
      
      <style jsx global>{`
        .scrollbar-custom::-webkit-scrollbar {
          width: 8px;
        }
        .scrollbar-custom::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 10px;
        }
        .scrollbar-custom::-webkit-scrollbar-thumb {
          background: #d1d5db;
          border-radius: 10px;
        }
        .scrollbar-custom::-webkit-scrollbar-thumb:hover {
          background: #9ca3af;
        }
      `}</style>
    </div>
  );
}