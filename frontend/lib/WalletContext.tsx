'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { PeraWalletConnect } from '@perawallet/connect';

interface WalletContextType {
  accountAddress: string | null;
  isConnected: boolean;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

// Instantiate once, outside the component, so it persists across renders
const peraWallet = new PeraWalletConnect();

export function WalletProvider({ children }: { children: ReactNode }) {
  const [accountAddress, setAccountAddress] = useState<string | null>(null);

  const connectWallet = async () => {
    try {
      const accounts = await peraWallet.connect();
      if (accounts.length > 0) {
        setAccountAddress(accounts[0]);
      }
    } catch (error: any) {
      if (error?.data?.type !== 'CONNECT_MODAL_CLOSED') {
        console.error('Connection failed:', error);
      }
    }
  };

  const disconnectWallet = () => {
    peraWallet.disconnect();
    setAccountAddress(null);
  };

  useEffect(() => {
    // Restore previous session if available
    peraWallet
      .reconnectSession()
      .then((accounts) => {
        if (accounts.length > 0) {
          setAccountAddress(accounts[0]);
        }
      })
      .catch(() => {
        // No prior session
        console.warn('No wallet session to reconnect');
      });

    return () => {
      peraWallet.connector?.off('disconnect');
    };
  }, []);

  const value: WalletContextType = {
    accountAddress,
    isConnected: accountAddress !== null,
    connectWallet,
    disconnectWallet,
  };

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>;
}

export function useWallet() {
  const context = useContext(WalletContext);
  if (context === undefined) {
    throw new Error('useWallet must be used within a WalletProvider');
  }
  return context;
}
