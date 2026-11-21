trigger AccountRiskTrigger on Account (after update) {
    for (Account recordItem : Trigger.new) {
        AccountRiskService.refresh(recordItem.Id);
    }
}
