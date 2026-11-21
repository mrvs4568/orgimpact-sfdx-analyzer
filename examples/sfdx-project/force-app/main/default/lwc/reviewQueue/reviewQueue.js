import { LightningElement } from 'lwc';
import STATUS_FIELD from '@salesforce/schema/Account.Review_Status__c';
export default class ReviewQueue extends LightningElement { statusField = STATUS_FIELD; }
