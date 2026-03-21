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
            fetch("http://0.0.0.0:8000/api/nodes/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                console.log("Node successfully mined to NeuroChain:", data);
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