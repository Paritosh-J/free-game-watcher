from pydantic import BaseModel, constr

class SubscribeIn(BaseModel):
    phone: constr(strip_whitespace=True, min_length=6, max_length=20) # type: ignore
    
class VerifyIn(BaseModel):
    phone: constr(strip_whitespace=True, min_length=6, max_length=20) # type: ignore
    code: constr(strip_whitespace=True, min_length=3, max_length=10) # type: ignore
    
class UnsubscribeIn(BaseModel):
    phone: constr(strip_whitespace=True, min_length=6, max_length=20) # type: ignore