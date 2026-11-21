public with sharing class AccountRiskService {
    public static Integer score(Id accountId) {
        List<Account> records = [SELECT Id, Health_Score__c FROM Account WHERE Id = :accountId LIMIT 1];
        if (records.isEmpty()) return 0;
        return records[0].Health_Score__c == null ? 0 : Integer.valueOf(records[0].Health_Score__c);
    }
    public static void refresh(Id accountId) {
        System.debug('Risk recalculation requested for ' + accountId);
    }
    public static String status() {
        return Schema.SObjectType.Account.fields.Review_Status__c.getDescribe().getLabel();
    }
}
