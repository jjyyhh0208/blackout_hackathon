import pymongo
from bson.objectid import ObjectId


class MongoClientHandler:
    def __init__(self, mongo_uri, database_name):
        """
        MongoClient 초기화
        """
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self.client = None
        self.db = None
        self.connect()

    def get_all_reviews(self):
        """
        school_review 컬렉션의 모든 리뷰를 리스트로 반환
        """
        try:
            collection = self.db["school_review"]
            reviews = list(collection.find())
            print(f"Retrieved {len(reviews)} reviews from school_review.")
            return reviews
        except Exception as e:
            print(f"Error retrieving reviews: {str(e)}")
            return []

    def get_all_schools(self):
        """
        school 컬렉션의 모든 학교 정보를 리스트로 반환
        """
        try:
            collection = self.db["exchange_school"]
            schools = list(collection.find())
            print(f"Retrieved {len(schools)} schools from school.")
            return schools
        except Exception as e:
            print(f"Error retrieving schools: {str(e)}")
            return []

    def connect(self):
        """
        MongoDB 연결
        """
        try:
            self.client = pymongo.MongoClient(self.mongo_uri)
            self.db = self.client[self.database_name]
            print(f"Connected to MongoDB database: {self.database_name}")
        except Exception as e:
            print(f"Error connecting to MongoDB: {str(e)}")
            raise

    def create(self, collection_name, document):
        """
        단일 문서 삽입
        """
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error inserting document: {str(e)}")
            return None

    def read(self, collection_name, filter_query=None, projection=None):
        """
        문서 조회
        """
        try:
            collection = self.db[collection_name]
            filter_query = filter_query or {}
            documents = list(collection.find(filter_query, projection))
            return documents
        except Exception as e:
            print(f"Error reading documents: {str(e)}")
            return []

    def update(self, collection_name, filter_query, update_values):
        """
        문서 업데이트
        """
        try:
            collection = self.db[collection_name]
            result = collection.update_many(filter_query, {"$set": update_values})
            return result.modified_count
        except Exception as e:
            print(f"Error updating documents: {str(e)}")
            return 0

    def delete(self, collection_name, filter_query):
        """
        문서 삭제
        """
        try:
            collection = self.db[collection_name]
            result = collection.delete_many(filter_query)
            return result.deleted_count
        except Exception as e:
            print(f"Error deleting documents: {str(e)}")
            return 0
