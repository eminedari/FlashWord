from flask import Flask,render_template, request,redirect,url_for,session,flash, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin,login_required, current_user

from queries import select,insert,update,delete

main = Blueprint('main',__name__)
auth = Blueprint('auth',__name__)

@main.route('/')
def index():
    user_count= select("count(*)","users")
    return render_template("index.html", user_count=user_count[0][0] )

@main.route('/update/user<id>', methods=['GET' ,'POST'])
def update_account(id):
    if request.method=='GET':
        userInfo= select("id,username,password,first_name,last_name,contact","users","id='{}'".format(id),asDict=True)
        return render_template("update_account.html",userInfo=userInfo)
    elif request.method=='POST':
        password = request.form.get('password')
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        email = request.form.get('email')
        password=generate_password_hash(password, method='sha256')

        #update attributes that dont require uniqueness
        update("users","password='{}',first_name='{}',last_name='{}'".format(password,firstName,lastName),
        "id='{}'".format(id))

        emailCheck =  select("id","users","contact='{}'".format(email),asDict=True)

        if bool(emailCheck) :
            flash('Email could not be changed, it already exists')
            return redirect(url_for('main.profile'))

        update("users","password='{}',first_name='{}',last_name='{}',contact='{}'".format(password,firstName,lastName,email),
        "id='{}'".format(id))
        flash("Acccount information is successfully updated")
        return redirect(url_for("main.profile"))

@main.route('/profile', methods=['GET' ,'POST'])
def profile():
    if request.method=="GET" :
        user_id = session["user_id"]
        userInfo= select("id,username,password,first_name,last_name,contact","users","id='{}'".format(user_id),asDict=True)
        return render_template("profile.html",userInfo=userInfo)
    if request.method=="POST" :
        if "delete" in request.form:
            delete("users","id='{}'".format(request.form.get("delete")))
            return redirect(url_for('main.index'))
        elif "update" in request.form:
            return redirect(url_for('main.update_account', id=request.form.get("update")))


@main.route('/library',methods=['GET','POST']) 
def library():
    if request.method=='GET':
        user_id= session['user_id']
        #get decks belonging to the user logined
        myDecks = select("id,title,front_lang,back_lang,quiz_score","decks","owning_user='{}'".format(user_id),asDict=True)
        #get the decks user have added
        addedDecks = select("decks.id,decks.title,decks.front_lang,decks.back_lang,decks.quiz_score",
        "decks join shared_decks on decks.id=shared_decks.deck_id",
        "shared_decks.user_id='{}'".format(user_id),asDict=True)
        return render_template("library.html",myDecks=myDecks,addedDecks=addedDecks,isMyDict=isinstance(myDecks,dict),isAddedDict=isinstance(addedDecks,dict))
    else:
        return redirect(url_for('main.create_deck'))
   


@main.route("/deck/<id>")
def deck_detail(id):
    #should show flashcards actually
    cards = select("id,front,back,belonging_deck","flashcards","belonging_deck='{}'".format(id),asDict=True)
    return render_template("deck_detail.html",cards=cards,isDict=isinstance(cards,dict),deck_id=id)


@main.route('/create_deck',methods=['GET','POST'])
def create_deck():
    if request.method == 'GET':
        return render_template("create_deck.html")
    else:
        title = request.form.get('title')
        front_lang = request.form.get('front_lang').lower()
        back_lang = request.form.get('back_lang').lower()
        keyword1 = request.form.get('keyword1').lower()
        keyword2 = request.form.get('keyword2').lower()
        if request.form.get('privacy'):#user have checked the box, deck will be private
            privacy = True
        else:
            privacy = False

        #languages table operations    

        fl = select("id","languages","name='{}'".format(front_lang),asDict=True)
        bl = select("id","languages","name='{}'".format(back_lang),asDict=True)

        if 'id' in fl:
            fl = fl['id']
        else :
            fl = insert("languages","name","'{}'".format(front_lang))
            fl = fl[0]

        if 'id' in bl:
            bl = bl['id']
        else :
            bl = insert("languages","name","'{}'".format(back_lang))
            bl = bl[0][0]   

        #get user_id
        user_id = session["user_id"]  

        #spoken_languages table operations
        speaks = select("user_id","spoken_languages","user_id='{}' and lang_id='{}'".format(user_id,fl),asDict=True)

        if 'user_id' in speaks:
            pass
        else :
            insert("spoken_languages","user_id,lang_id","'{}','{}'".format(user_id,fl),returnID = False)


        #keywords table operations
        k1 = select("id","keywords","keyword='{}'".format(keyword1),asDict=True)
        k2 = select("id","keywords","keyword='{}'".format(keyword2),asDict=True)

        if 'id' in k1:
            k1 = k1['id']
        else :
            k1 = insert("keywords","keyword","'{}'".format(keyword1))
            k1 = k1[0][0]
       

        if 'id' in k2:
            k2 = k2['id']
        else :
            k2 = insert("keywords","keyword","'{}'".format(keyword2))
            k2= k2[0][0]
        


        #create the deck with the inputs from user
        #quiz default 0 sonradan ekledim dikkat
        deck_id = insert(table="decks",columns="title,front_lang,back_lang,privacy,owning_user",
        values="'{}','{}','{}','{}','{}'".format(title,fl,bl,privacy,user_id))


        #insert deck-keyword combination to table 
        insert("deck_keyword","deck_id,keyword_id","{},{}".format(int(deck_id[0][0]),int(k1)),returnID=False)
        insert("deck_keyword","deck_id,keyword_id","{},{}".format(int(deck_id[0][0]),int(k2)),returnID=False)

        #finally return to library
        return redirect(url_for('main.library'))

@main.route('/delete_deck/<id>')
def delete_deck(id):
    #delete the deck
    delete("decks","id='{}'".format(id))
    #return back to library
    return redirect(url_for('main.library'))


@main.route('/delete_card/<id>')
def delete_card(id):
    #delete the deck
    delete("flashcards","id='{}'".format(id))
    #return back to library
    return redirect(url_for('main.library'))

@main.route('/update_card/<id>',methods=['GET','POST'])
def update_card(id):
    cardInfo = select("id,front,back,belonging_deck","flashcards","id='{}'".format(id),asDict=True)
    if request.method=='GET':
        return render_template("update_card.html",cardInfo=cardInfo)
    else:
        front = request.form.get('front')
        back = request.form.get('back')
        update("flashcards","front='{}',back='{}'".format(front,back),"id='{}'".format(id))
        
        #return back to library
        return redirect(url_for('main.deck_detail',id=cardInfo['belonging_deck']))    

@main.route('/quiz/<deck_id>',methods=['GET','POST'])
def quiz(deck_id):
    cards=select("front,back","flashcards","belonging_deck='{}'".format(deck_id))
    if request.method=='GET':
        return render_template("quiz.html",deck_id=deck_id,cards=cards)
    else:
        score=0
        for card in cards:
            answer = request.form.get(card[0])
            if answer == card[1]:
                score=score+1
        update("decks","quiz_score='{}'".format(score),"id='{}'".format(deck_id))
        return redirect(url_for('main.library'))




@main.route('/add_card/<deck_id>',methods=['GET','POST'])
def add_card(deck_id):
    if request.method=='GET':
        return render_template("add_card.html",deck_id=deck_id)
    else:
        if "add" in request.form:
            #add the card, stay in the same page
            front = request.form.get('front')
            back = request.form.get('back')         
            insert("flashcards", "front,back,belonging_deck", "'{}','{}','{}'".format(front,back,deck_id))
            update("decks","card_count=card_count+1","id='{}'".format(deck_id))
            return render_template("add_card.html",deck_id=deck_id)

        elif "library" in request.form:
            #return to library
            return redirect(url_for('main.library'))



@main.route('/search',methods=['GET','POST'])
def search():
    decks=None
    keywords = select("id,keyword","keywords",asDict=True)
    if request.method == 'GET':
        return render_template("search.html",keywords=keywords,decks=decks, isDict=True)
    else:
        key_id= request.form.get('key')

        decks =select("decks.id,decks.title,decks.front_lang,decks.back_lang,decks.card_count,decks.privacy",
        "decks join deck_keyword on decks.id=deck_keyword.deck_id",
        "deck_keyword.keyword_id='{}'".format(key_id),asDict=True)
        print(decks)
        return render_template("search.html", keywords=keywords, decks=decks,isDict=isinstance(decks,dict))


@main.route('/add_shared/<deck_id>')
def add_shared(deck_id):
    user_id= session["user_id"]
    #add the deck to shared_decks table
    insert("shared_decks","user_id,deck_id","'{}','{}'".format(user_id,deck_id),returnID=False)
    #return back to library
    return redirect(url_for('main.library'))

@auth.route('/login', methods=['GET'])
def login():
    return render_template("login.html")

@auth.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    userCheck = select("username","users","username='{}'".format(username),asDict=True)
    passwordCheck =  select("password","users","username='{}'".format(username),asDict=True)    

    # check if the user actually exists
    if not userCheck or not check_password_hash(passwordCheck['password'], password):
        flash('Please check your login details and try again.')
         # if the user doesn't exist or password is wrong, reload the page
        return redirect(url_for('auth.login'))

    # if the above check passes, then we know the user has the right credentials
    userInfo =select("id,first_name,last_name","users","username='{}'".format(username),asDict=True)
    session["username"] = username
    session["user_id"] = userInfo['id']
    session["first_name"] = userInfo['first_name']
    return redirect(url_for('main.profile'))#,userInfo=userInfo))


@auth.route('/signup', methods=['GET'])
def signup():
    return render_template("signup.html")


@auth.route('/signup', methods=['POST'])
def signup_post():
    username = request.form.get('username')
    password = request.form.get('password')
    firstName = request.form.get('firstName')
    lastName = request.form.get('lastName')
    email = request.form.get('email')
    #select(columns,table,where,asDict)
    usernameCheck = select("username","users","username='{}'".format(username),asDict=True)
    emailCheck =  select("id","users","contact='{}'".format(email),asDict=True)

    if bool(usernameCheck) :#if the dictionary is empty, bool returns false
        flash('Username already exists')
         # if a username is found, we want to redirect back to signup page so user can try again
        return redirect(url_for('auth.signup'))
    if bool(emailCheck) :
        flash('Email already exists')
        return redirect(url_for('auth.signup'))

    #Add the new user to the database, Hash the password. 
    password=generate_password_hash(password, method='sha256')
    insert(table="users",columns="username,password,first_name,last_name,contact",values="'{}','{}','{}','{}','{}'".format(username,password,firstName,lastName,email))
    #redirect to login page after signing up the new user
    return redirect(url_for('auth.login'))


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))