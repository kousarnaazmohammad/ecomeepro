from itsdangerous import URLSafeTimedSerializer #
from key import salt
def encode(data):
    serializer=URLSafeTimedSerializer("Kousar@1")
    return serializer.dumps(data,salt=salt)
def decode(data):
    serializer=URLSafeTimedSerializer("Kousar@1")
    return serializer.loads(data,salt=salt)
