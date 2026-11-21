public with sharing class AccountRiskController {
    @AuraEnabled(cacheable=true)
    public static Integer score(Id accountId) {
        return AccountRiskService.score(accountId);
    }
}
