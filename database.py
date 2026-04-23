import boto3
from botocore.exceptions import ClientError

class DuplicateHandler:
    def __init__(self, table_name="ProcessedTrades"):
        self.table = boto3.resource('dynamodb').Table(table_name)

    def already_processed(self, internal_id: str) -> bool:
        try:
            response = self.table.get_item(Key={'trade_id': internal_id})
            return 'Item' in response
        except ClientError:
            return False

    def mark_processed(self, internal_id: str, data: dict):
        self.table.put_item(Item={'trade_id': internal_id, **data})