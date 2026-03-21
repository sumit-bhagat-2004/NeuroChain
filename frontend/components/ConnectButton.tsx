import { useEffect, useState } from "react";
import { PeraWalletConnect } from "@perawallet/connect";

// Instantiate once, outside the component, so it persists across renders
const peraWallet = new PeraWalletConnect();

export default function LoginButton() {
  const [accountAddress, setAccountAddress] = useState<string | null>(null);

  const connectWallet = async () => {
    try {
      const accounts = await peraWallet.connect(); // ✅ call .connect() on the instance
      setAccountAddress(accounts[0]);
    } catch (error: any) {
      if (error?.data?.type !== "CONNECT_MODAL_CLOSED") {
        console.error("Connection failed:", error);
      }
    }
  };

  const disconnectWallet = () => {
    peraWallet.disconnect(); // ✅ not async, no need to await
    setAccountAddress(null);
  };

  useEffect(() => {
    // ✅ Use reconnectSession() — the correct SDK method for restoring sessions
    peraWallet
      .reconnectSession()
      .then((accounts) => {
        if (accounts.length) {
          setAccountAddress(accounts[0]);
        }
      })
      .catch((error) => {
        // Ignore — no prior session
        console.warn("No session to reconnect:", error);
      });

    // ✅ Clean up the modal/listeners when the component unmounts
    return () => {
      peraWallet.connector?.off("disconnect");
    };
  }, []);

  return (
    <div>
      {accountAddress ? (
        <div>
          <p>Connected: {accountAddress}</p>
          <button onClick={disconnectWallet}>Disconnect</button>
        </div>
      ) : (
        <button onClick={connectWallet}>Connect to Pera Wallet</button>
      )}
    </div>
  );
}
