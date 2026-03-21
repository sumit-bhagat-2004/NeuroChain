// content.js: V8 - Flawless De-Duplication Engine

console.log("🟢 NeuroChain V8 Core Extractor Injected (De-Duplication Engine).");

if (window.location.hostname === "localhost") {
    setInterval(() => {
        const peraData = window.localStorage.getItem('PeraWallet.Wallet');
        if (peraData) {
            try {
                const parsed = JSON.parse(peraData);
                if (parsed.accounts && parsed.accounts.length > 0) {
                    const walletId = parsed.accounts[0];
                    chrome.runtime.sendMessage(
                        { type: "SYNC_WALLET", wallet: walletId }, 
                        () => { if (chrome.runtime.lastError) {} }
                    );
                }
            } catch (e) { console.error("NeuroChain: Failed to parse Pera storage"); }
        }
    }, 3000);
}

// ==========================================
// SCENARIO 2: Scraping Data from Google Meet
// ==========================================
if (window.location.hostname === "meet.google.com") {
    
    // Auto-Turn on Captions
    setTimeout(() => {
        const captionBtn = document.querySelector('button[aria-label*="Turn on captions"], button[aria-label*="captions"]');
        if (captionBtn) {
            captionBtn.click();
            console.log("🟢 NeuroChain V8: Captions auto-enabled.");
        }
    }, 8000);

    const sentSentences = new Set();
    let lastChatText = "";
    let lastRamblingSent = "";

    // 1. VOICE EXTRACTION (Flawless Set Strategy)
    setInterval(() => {
        // Target specifically the classes your Meet instance is using for the active text bubble
        const nodes = document.querySelectorAll('.ygicle, .VbkSUe, .CNusmb, [jsname="YSxPC"]');
        if (nodes.length === 0) return;

        // Grab ONLY the very last node to prevent parent-child duplication
        const latestBubble = nodes[nodes.length - 1];
        let text = latestBubble.textContent ? latestBubble.textContent : "";
        
        // Clean UI artifacts and the prepended "You" string
        text = text.replace(/content_copy/g, '')
                   .replace(/arrow_downwardJump to bottom/g, '')
                   .replace(/^You/g, '')
                   .trim();

        if (!text) return;

        // Step A: Extract all mathematically finalized thoughts (sentences)
        const sentences = text.match(/[^.!?]+[.!?]+/g) || [];
        let completedTextLength = 0;

        sentences.forEach(sentence => {
            const cleanSentence = sentence.trim();
            completedTextLength += sentence.length;
            
            // If it's a real sentence and hasn't been sent yet, fire it to FastAPI!
            if (cleanSentence.length > 5 && !sentSentences.has(cleanSentence)) {
                sendToNeuroChain(cleanSentence, "meet_voice");
                sentSentences.add(cleanSentence);
                
                // Memory management: keep extension lightweight
                if (sentSentences.size > 200) {
                    sentSentences.delete(sentSentences.values().next().value);
                }
            }
        });

        // Step B: Handle Rambling (text that doesn't have punctuation yet)
        const tail = text.substring(completedTextLength).trim();
        
        if (tail.length > 70) {
            // Only send the rambling chunk if it has grown significantly (prevents spamming every 2s)
            if (!lastRamblingSent || !tail.includes(lastRamblingSent) || tail.length > lastRamblingSent.length + 25) {
                sendToNeuroChain(tail + "...", "meet_voice");
                lastRamblingSent = tail;
            }
        }
        
        // Reset rambling tracker if the user finally drops a period.
        if (tail.length < 10) {
            lastRamblingSent = "";
        }

    }, 2000);

    // 2. CHAT EXTRACTION 
    setInterval(() => {
        const chatSelectors = [
            '.oIy2qc', '.Zmm6We', '.poRWVK', '.beMhkf',
            '[data-message-text]', 'div[data-sender-id]',
            '.ptNLrf', '.chmVPb', '[jsname="dTKtvb"]'
        ].join(', ');

        const chatNodes = document.querySelectorAll(chatSelectors);
        
        if (chatNodes.length > 0) {
            const latestChat = chatNodes[chatNodes.length - 1];
            let text = latestChat.textContent ? latestChat.textContent.trim() : "";
            text = text.replace("Pin message", "").trim();
            
            if (text && text !== lastChatText && text.length > 0) {
                sendToNeuroChain(text, "meet_chat");
                lastChatText = text;
            }
        }
    }, 2000);

    function sendToNeuroChain(text, source) {
        console.log(`[NeuroChain V8] Extracted ${source}:`, text);
        
        try {
            chrome.runtime.sendMessage(
                { type: "NEW_NODE_DATA", payload: { text: text, source: source } },
                () => { if (chrome.runtime.lastError) {} }
            );
        } catch (e) {
            console.debug("[NeuroChain V8] Extension context asleep.");
        }
    }
}