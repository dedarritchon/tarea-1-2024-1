from typing import Union, Optional, List, Annotated
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import datetime

import random

app = FastAPI()

origins = [
    "https://tarea-1-2024-1.onrender.com",
    "http://localhost:8888",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

class User(BaseModel):
    id: str
    username: str
    password: str
    avatar: str = ''
    created: Optional[str] = None

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
    image: Optional[str] = None
    created: Optional[str] = None
    userId: str

class CreatePostRequest(BaseModel):
    title: str
    content: str
    image: Optional[str] = None

class Comment(BaseModel):
    id: str
    content: str
    created: Optional[str] = None
    postId: str
    userId: str

class CreateCommentRequest(BaseModel):
    content: str
    postId: str

class Friendship(BaseModel):
    id: str
    userId: str
    friendId: str
    status: str = 'pending'
    created: Optional[str] = None


class createFriendshipRequest(BaseModel):
    friendId: str

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


@app.get("/api/reset")
def reset_state():
    userDatabase.reset()
    postDatabase.reset()
    commentDatabase.reset()
    friendshipDatabase.reset()
    userSessionDatabase.reset()
    return {}

def generate_random_id():
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))

@app.post("/api/users", response_model=User, tags=["users"])
def create_user(createUserPayload: CreateUserRequest):
    
    existing_user = userDatabase.get_user_by_username(createUserPayload.username)

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        id=generate_random_id(),
        username=createUserPayload.username,
        password=createUserPayload.password,
        avatar=createUserPayload.avatar,
        created=datetime.datetime.now().isoformat()
    )

    userDatabase.add_user(user)

    return user

@app.post("/api/login", response_model=LoginResponse, tags=["login"])
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


@app.get("/api/users", response_model=List[User], tags=["users"])
def get_users(authorization: Annotated[str, Header()]):
    user = getUserFromSession(authorization)
    return userDatabase.users


@app.get("/api/posts", response_model=List[Post], tags=["posts"])
def get_posts(authorization: Annotated[str, Header()], title: str = '', userId: str = ''):

    user = getUserFromSession(authorization)

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

@app.get("/api/user", response_model=User, tags=["users"])
def get_current_user(authorization: Annotated[str, Header()]):
    user = getUserFromSession(authorization)
    return user

@app.post("/api/posts", response_model=Post, tags=["posts"])
def create_post(ceatePostPayload: CreatePostRequest, authorization: Annotated[str, Header()]):

    user = getUserFromSession(authorization)

    post = Post(
        id=generate_random_id(),
        title=ceatePostPayload.title,
        content=ceatePostPayload.content,
        image=ceatePostPayload.image,
        userId=user.id,
        created=datetime.datetime.now().isoformat()
    )

    postDatabase.add_post(post)

    return post

@app.post("/api/comments", response_model=Comment, tags=["comments"])
def create_comment(createCommentPayload: CreateCommentRequest, authorization: Annotated[str, Header()]):

    user = getUserFromSession(authorization)

    comment = Comment(
        id=generate_random_id(),
        content=createCommentPayload.content,
        postId=createCommentPayload.postId,
        userId=user.id,
        created=datetime.datetime.now().isoformat()
    )

    commentDatabase.add_comment(comment)

    return comment

@app.get("/api/comments", response_model=List[Comment], tags=["comments"])
def get_comments(postId: str):
    return [comment for comment in commentDatabase.comments if comment.postId == postId]


@app.post("/api/friendships", response_model=Friendship, tags=["friendships"])
def create_friendship(createFriendshipPayload: createFriendshipRequest, authorization: Annotated[str, Header()]):

    user = getUserFromSession(authorization)

    friendship = Friendship(
        id=generate_random_id(),
        userId=user.id,
        friendId=createFriendshipPayload.friendId,
        created=datetime.datetime.now().isoformat()
    )

    friendshipDatabase.add_friendship(friendship)

    return friendship

@app.get("/api/friendships", response_model=List[Friendship], tags=["friendships"])
def get_friendships(authorization: Annotated[str, Header()]):
    user = getUserFromSession(authorization)
    return [friendship for friendship in friendshipDatabase.friendships if friendship.userId == user.id or friendship.friendId == user.id]

@app.put("/api/friendships/{id}", response_model=Friendship, tags=["friendships"])
def update_friendship(id: str, acceptFriendshipPayload: updateFriendshipRequest, authorization: Annotated[str, Header()]):

    user = getUserFromSession(authorization)

    friendship = friendshipDatabase.get_friendship(id)

    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")

    if friendship.userId != user.id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    friendship.status = acceptFriendshipPayload.status

    return friendship

@app.get("/api/friendships/recommendations", response_model=List[User], tags=["friendships"])
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

def generate_random_content():
    return ''.join(random.choices('lorem ipsum dolor sit amet, consectetur adipiscing elit. ', k=50))

@app.get("/api/populate", tags=["populate"])
def populate():
    # create 10, users, 10 posts, 10 comments, 10 friendships
    userDatabase.reset()
    postDatabase.reset()
    commentDatabase.reset()
    friendshipDatabase.reset()

    for i in range(10):
        user = User(
            id=generate_random_id(),
            username=f'user{i}',
            password=f'pass{i}',
            avatar=f"https://cdn-icons-png.flaticon.com/256/21/2110{i}.png",
            created=datetime.datetime.now().isoformat()
        )
        userDatabase.add_user(user)

    for i in range(10):
        image = f"https://source.unsplash.com/random/200x200?sig={i+1}"
        post = Post(
            id=generate_random_id(),
            title=f'post{i}',
            content=generate_random_content(),
            userId=userDatabase.users[i].id,
            created=datetime.datetime.now().isoformat(),
            image=image if i % 2 == 0 else None
        )
        postDatabase.add_post(post)
        
    for i in range(10):
        comment = Comment(
            id=generate_random_id(),
            content=generate_random_content(),
            postId=postDatabase.posts[i].id,
            userId=userDatabase.users[9-i].id,
            created=datetime.datetime.now().isoformat()
        )
        commentDatabase.add_comment(comment)

    for i in range(9):
        status = 'accepted' if i % 2 == 0 else 'pending'
        friendship = Friendship(
            id=generate_random_id(),
            userId=userDatabase.users[i].id,
            friendId=userDatabase.users[i+1].id,
            status=status,
            created=datetime.datetime.now().isoformat()
        )
        friendshipDatabase.add_friendship(friendship)

    return {
        "users": userDatabase.users,
        "posts": postDatabase.posts,
        "comments": commentDatabase.comments,
        "friendships": friendshipDatabase.friendships
    }

@app.get("/frontend", response_class=HTMLResponse, tags=["frontend"])
# return html template
def frontend():
    # Open and read the HTML file
    with open("templates/index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)
