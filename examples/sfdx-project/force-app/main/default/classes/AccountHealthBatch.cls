public with sharing class AccountHealthBatch {
    public static void recalculate(Id accountId) {
        AccountRiskService.refresh(accountId);
    }
}
