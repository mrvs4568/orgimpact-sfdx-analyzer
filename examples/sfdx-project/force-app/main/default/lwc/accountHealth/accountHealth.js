import { LightningElement, api, wire } from 'lwc';
import getScore from '@salesforce/apex/AccountRiskController.score';
import HEALTH_FIELD from '@salesforce/schema/Account.Health_Score__c';

export default class AccountHealth extends LightningElement {
    @api recordId;
    healthField = HEALTH_FIELD;
    @wire(getScore, {accountId: '$recordId'}) score;
}
