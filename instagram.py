import requests
from itertools import chain


def get_session(session_id, app_id, user_id, user_agent):
    for i in (session_id, app_id, user_id):
        assert isinstance(i, str)
    s = requests.Session()
    s.cookies["sessionid"] = session_id
    s.headers["X-IG-App-ID"] = app_id
    s.cookies["ds_user_id"] = user_id
    s.headers["user-agent"] = user_agent
    return s


class User:
    @staticmethod
    def fetch(s, username):
        return User(s.get(
            f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        ).json()["data"]["user"])

    def __init__(self, data):
        for k, v in data.items():
            if hasattr(self, k):
                self.__setattr__(f"{k}_", v)
            else:
                self.__setattr__(k, v)
        self.raw = data

    @staticmethod
    def by_id(id_):
        return User({"id": id_})


def get_following(s, user: User):
    users = []
    max_id = 0
    while max_id is not None:
        users.append(s.get(f"https://www.instagram.com/api/v1/friendships/{user.id}/following/?max_id={max_id}").json())
        max_id = users[-1].get("next_max_id")

    return (
        User.fetch(s, u["username"])
        for u in chain(*map(lambda l: l["users"], users))
    )

if __name__ == "__main__":
    from argparse import ArgumentParser

    argp = ArgumentParser(prog="instagram.py")
    argp.add_argument("session_id", type=str)
    argp.add_argument("app_id", type=str)
    argp.add_argument("user_id", type=str)
    argp.add_argument("user_agent", type=str)
    argp.add_argument("-q", default=False, help="print only if user doesn't follow back")

    args = argp.parse_args()
    session = get_session(args.session_id, args.app_id, args.user_id, args.user_agent)
    output = {}
    for i in get_following(session, User.by_id(args.user_id)):
        assert i.followed_by_viewer
        output[i.username] = {
            "follow_back": i.follows_viewer,
            "full_name": i.full_name
        }

        if not i.follows_viewer:
            print(f"{i.username:>25s}: DOESN'T FOLLOW BACK")
        elif not args.q:
            print(f"{i.username:>25s}: follows back")

    from json import dump
    dump(output, open("output2.json", "w+"), indent=4)
