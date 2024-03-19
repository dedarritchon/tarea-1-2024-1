from typing import Union, Optional, List, Annotated
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header

app = FastAPI()


class User(BaseModel):
    id: int
    username: str
    password: str
    avatar: str = ''
    created_at: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str


class UserSession(BaseModel):
    user: User
    token: str

class CreateUserRequest(LoginRequest):
    avatar: str = ''

class Post(BaseModel):
    id: str
    title: str
    content: str
    created: Optional[str] = None
    userId: int

class CreatePostRequest(BaseModel):
    title: str
    content: str

class Comment(BaseModel):
    id: int
    content: str
    created: Optional[str] = None
    postId: int
    userId: int

class CreateCommentRequest(BaseModel):
    content: str
    postId: int

class Friendship(BaseModel):
    id: int
    userId: int
    friendId: int
    status: str = 'pending'
    created: Optional[str] = None


class createFriendshipRequest(BaseModel):
    friendId: int

class updateFriendshipRequest(BaseModel):
    status: str


class UserDatabase():

    def __init__(self):
        self.users = []
    
    def reset(self):
        self.users = []

    def add_user(self, user: User):
        self.users.append(user)
    
    def get_user(self, id: int):
        for user in self.users:
            if user.id == id:
                return user
        raise HTTPException(status_code=404, detail="User not found")

    def get_user_by_username(self, username: str):
        for user in self.users:
            if user.username == username:
                return user
        raise HTTPException(status_code=404, detail="User not found")

    def delete_user(self, id: int):
        for user in self.users:
            if user.id == id:
                self.users.remove(user)
                return True
        return False


class UserSessionDatabase():

    def __init__(self):
        self.sessions = []

    def reset(self):
        self.sessions = []

    def add_session(self, session: UserSession):
        self.sessions.append(session)
    
    def get_session(self, token: str):
        token = token.replace('Bearer ', '')
        for session in self.sessions:
            if session.token == token:
                return session
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    def delete_session(self, token: str):
        for session in self.sessions:
            if session.token == token:
                self.sessions.remove(session)
                return True
        raise HTTPException(status_code=401, detail="Unauthorized")


class PostDatabase():

    def __init__(self):
        self.posts = []
    
    def reset(self):
        self.posts = []

    def add_post(self, post: Post):
        self.posts.append(post)
    
    def get_post(self, id: int):
        for post in self.posts:
            if post.id == id:
                return post
        raise HTTPException(status_code=404, detail="Post not found")
 
    def delete_post(self, id: int):
        for post in self.posts:
            if post.id == id:
                self.posts.remove(post)
                return True
        return False


class CommentDatabase():

    def __init__(self):
        self.comments = []
    
    def reset(self):
        self.comments = []

    def add_comment(self, comment: Comment):
        self.comments.append(comment)
    
    def get_comment(self, id: int):
        for comment in self.comments:
            if comment.id == id:
                return comment
        raise HTTPException(status_code=404, detail="Comment not found")
    
    def delete_comment(self, id: int):
        for comment in self.comments:
            if comment.id == id:
                self.comments.remove(comment)
                return True
        return False


class FriendshipDatabase():

    def __init__(self):
        self.friendships = []

    def reset(self):
        self.friendships = []

    def add_friendship(self, friendship: Friendship):
        self.friendships.append(friendship)
    
    def get_friendship(self, id: int):
        for friendship in self.friendships:
            if friendship.id == id:
                return friendship
        raise HTTPException(status_code=404, detail="Friendship not found")
    
    def delete_friendship(self, id: int):
        for friendship in self.friendships:
            if friendship.id == id:
                self.friendships.remove(friendship)
                return True
        return False


userDatabase = UserDatabase()
postDatabase = PostDatabase()
commentDatabase = CommentDatabase()
friendshipDatabase = FriendshipDatabase()
userSessionDatabase = UserSessionDatabase()


@app.get("/reset")
def reset_state():
    userDatabase.reset()
    postDatabase.reset()
    commentDatabase.reset()
    friendshipDatabase.reset()
    userSessionDatabase.reset()
    return {}

def generate_random_id():
    import random
    # with letters and numbers
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))

@app.post("/users", response_model=User, tags=["users"])
def create_user(createUserPayload: CreateUserRequest):
    
    existing_user = userDatabase.get_user_by_username(createUserPayload.username)

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        id=generate_random_id(),
        username=createUserPayload.username,
        password=createUserPayload.password,
        avatar=createUserPayload.avatar
    )

    userDatabase.add_user(user)

    return user

@app.post("/login", response_model=LoginResponse, tags=["login"])
def login(loginPayload: LoginRequest):
    
    user = userDatabase.get_user_by_username(loginPayload.username)

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if user.password != loginPayload.password:
        raise HTTPException(status_code=400, detail="Invalid password")

    token = generate_random_id()

    userSession = UserSession(user=user, token=token)

    userSessionDatabase.add_session(userSession)

    return LoginResponse(token=token)


@app.get("/users", response_model=List[User], tags=["users"])
def get_users():
    return userDatabase.users


@app.get("/posts", response_model=List[Post], tags=["posts"])
def get_posts(title: str = '', userId: int = None):
    allPosts = postDatabase.posts

    if title:
        allPosts = [post for post in allPosts if title in post.title]
    
    if userId:
        allPosts = [post for post in allPosts if post.userId == userId]
    
    return allPosts

def getUserFromSession(authorization: str):
    userSession = userSessionDatabase.get_session(authorization)
    if not userSession:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return userSession.user

@app.post("/posts", response_model=Post, tags=["posts"])
def create_post(ceatePostPayload: CreatePostRequest, authorization: Annotated[str, Header()]):

    user = getUserFromSession(authorization)

    post = Post(
        id=generate_random_id(),
        title=ceatePostPayload.title,
        content=ceatePostPayload.content,
        userId=user.id
    )

    postDatabase.add_post(post)

    return post

@app.post("/comments", response_model=Comment, tags=["comments"])
def create_comment(createCommentPayload: CreateCommentRequest, authorization: Annotated[str, Header()]):

    user = getUserFromSession(authorization)

    comment = Comment(
        id=generate_random_id(),
        content=createCommentPayload.content,
        postId=createCommentPayload.postId,
        userId=user.id
    )

    commentDatabase.add_comment(comment)

    return comment

@app.get("/comments", response_model=List[Comment], tags=["comments"])
def get_comments(postId: int):
    return [comment for comment in commentDatabase.comments if comment.postId == postId]


@app.post("/friendships", response_model=Friendship, tags=["friendships"])
def create_friendship(createFriendshipPayload: createFriendshipRequest, authorization: Annotated[str, Header()]):

    user = getUserFromSession(authorization)

    friendship = Friendship(
        id=generate_random_id(),
        userId=user.id,
        friendId=createFriendshipPayload.friendId
    )

    friendshipDatabase.add_friendship(friendship)

    return friendship

@app.get("/friendships", response_model=List[Friendship], tags=["friendships"])
def get_friendships(userId: int):
    return [friendship for friendship in friendshipDatabase.friendships if friendship.userId == userId]

@app.post("/friendships/{id}", response_model=Friendship, tags=["friendships"])
def update_friendship(id: int, acceptFriendshipPayload: updateFriendshipRequest, authorization: Annotated[str, Header()]):

    user = getUserFromSession(authorization)

    friendship = friendshipDatabase.get_friendship(id)

    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")

    if friendship.friendId != user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    friendship.status = acceptFriendshipPayload.status

    return friendship

@app.get("/friendships/recommendations", response_model=List[User], tags=["friendships"])
def get_friendship_recommendations(authorization: Annotated[str, Header()]):

    user = getUserFromSession(authorization)

    friendships = friendshipDatabase.friendships

    recommendations = []

    all_users = userDatabase.users

    # give me the users that are not friends with me and are friends with my friends

    for u in all_users:
        if u.id == user.id:
            continue
        is_friend = False
        for f in friendships:
            if f.userId == user.id and f.friendId == u.id:
                is_friend = True
                break
        if is_friend:
            continue
        is_friend_of_friend = False
        for f in friendships:
            if f.userId == user.id:
                for f2 in friendships:
                    if f2.userId == f.friendId and f2.friendId == u.id:
                        is_friend_of_friend = True
                        break
        if is_friend_of_friend:
            recommendations.append(u)

    return recommendations
