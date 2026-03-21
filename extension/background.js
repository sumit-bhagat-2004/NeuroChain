// background.js: Acts as the secure bridge between the Web page and FastAPI

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    
    // 1. Handle Wallet Sync from Next.js
    if (message.type === "SYNC_WALLET") {
        chrome.storage.local.set({ neurochain_wallet: message.wallet }, () => {
            console.log("NeuroChain Wallet Synced:", message.wallet);
            sendResponse({ status: "success" });
        });
        return true; // Keep message channel open for async response
    }

    // 2. Handle Data from Google Meet
    if (message.type === "NEW_NODE_DATA") {
        // Retrieve the stored wallet address before sending to FastAPI
        chrome.storage.local.get(['neurochain_wallet'], (result) => {
            const wallet = result.neurochain_wallet || "anonymous";

            const payload = {
                text: message.payload.text,
                source: message.payload.source,
                author_wallet: wallet
            };

            // Call FastAPI Backend
            fetch("http://localhost:8000/api/nodes/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                console.log("Node successfully mined to NeuroChain:", data);

                // Log evolution information if available
                if (data.action === "merged" && data.merge_count > 0) {
                    console.log(`💡 Thought evolved! (${data.merge_count} evolution${data.merge_count > 1 ? "s" : ""}, creativity: ${(data.creativity_score * 100).toFixed(0)}%)`);
                }

                // Log similarity breakdown if available
                if (data.similarity_breakdown) {
                    console.log("Similarity breakdown:", {
                        semantic: (data.similarity_breakdown.semantic * 100).toFixed(0) + "%",
                        keyword: (data.similarity_breakdown.keyword * 100).toFixed(0) + "%",
                        fuzzy: (data.similarity_breakdown.fuzzy * 100).toFixed(0) + "%",
                        confidence: data.similarity_breakdown.confidence
                    });
                }

                sendResponse({ status: "success", data: data });
            })
            .catch(err => {
                console.error("NeuroChain API Error:", err);
                sendResponse({ status: "error", message: err.toString() });
            });
        });

        // CRITICAL FIX: Tell Chrome we will send the response asynchronously!
        return true; 
    }
});