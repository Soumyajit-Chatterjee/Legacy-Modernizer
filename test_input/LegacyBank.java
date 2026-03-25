package com.legacy.bank;

public class LegacyBank {

    /**
     * Process a transaction.
     * This is a very old and legacy comment block.
     * We need to strip this out.
     */
    public boolean processTransaction(String accountId, double amount) {
        // Step 1: Validate
        if (!validateAccount(accountId)) {
            return false;
        }
        
        // Step 2: Check balance
        double currentBalance = getBalance(accountId);
        if (currentBalance < amount) {
            System.out.println("Insufficient funds!");
            return false;
        }
        
        /* 
         * Step 3: Deduct
         */
        updateBalance(accountId, currentBalance - amount);
        
        // Step 4: Record
        recordAudit(accountId, amount);
        
        return true;
    }

    private boolean validateAccount(String accountId) {
        // Simulated DB call
        return accountId != null && accountId.length() == 10;
    }

    private double getBalance(String accountId) {
        // Simulated DB call returning some dummy value
        return 500.00;
    }

    private void updateBalance(String accountId, double newBalance) {
        // Simulated DB update
        System.out.println("Updating balance for " + accountId + " to " + newBalance);
    }

    private void recordAudit(String accountId, double amount) {
        // Logs audit to an old table
        System.out.println("Audit: Deducted " + amount + " from " + accountId);
    }
}
