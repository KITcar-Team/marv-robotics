# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import ldap
import base64
import bcrypt
import fcntl
import json
import os
import time

import flask
import jwt
from flask import current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from marv import utils
from marv.model import User, Group, db
from .tooling import api_group as marv_api_group

def ldap_auth(username, password):
    try:
        ldap_connection = ldap.initialize('ldap://kitcar_ldap_daemon:389')
        ldap_connection.protocol_version = ldap.VERSION3
        ldap_connection.simple_bind_s("uid=" + username +",ou=users,dc=kitcar-team,dc=de", password)
        ldap_connection.unbind_s()
        return True
    except ldap.INVALID_CREDENTIALS:
        print("invalide credentials")
        return False
    except ldap.SERVER_DOWN:
        print("server is currently not available")
        return False

# TODO: switch to idempotent OR IGNORE (like tag.py)
# TODO: move (part) of this to site
class UserManager(object):
    def __init__(self):
        pass

    def authenticate(self, username, password):
        if not username or not password:
            return False
        if ldap_auth(username, password): # Ldap authentification = true?
            print("ldap credentials correct\n")
            user = None
            try:
                #this is from the newest version... did they change the database??
                #user = db.session.query(User).filter_by(name=username, realm='marv').one()
                user = db.session.query(User).filter_by(name=username).one()
                print("marv db found user credentials correct\n")
                return True
            except NoResultFound:
                # this is the first time the user is logging in, lets create a pseudo account
                print("marv db no user found\n")
                name = username.split('.')
                self.user_add(username, "password", username, name[0], name[1])
                # now the user exists, lets try again
                self.group_adduser("admin", username)
                try:
                    user = db.session.query(User).filter_by(name=username).one()
                    print("marv db found user credentials correct\n")
                    return True
                except NoResultFound:
                    print("marv db didnt found user I just created? wtf?\n")
                    return False

    def user_add(self, name, password, realm, realmuid, given_name=None, family_name=None,
                 email=None, time_created=None, time_updated=None, _restore=None):
        try:
            if not _restore:
                password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            now = int(utils.now())
            if not time_created:
                time_created = now
            if not time_updated:
                time_updated = now
            user = User(name=name, password=password, realm=realm, given_name=given_name,
                        family_name=family_name, email=email, realmuid=realmuid,
                        time_created=time_created, time_updated=time_updated)
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            raise ValueError('User {} exists already'.format(name))

    def user_rm(self, username):
        try:
            user = db.session.query(User).filter_by(name=username).one()
            db.session.delete(user)
            db.session.commit()
        except NoResultFound:
            raise ValueError('User {} does not exist'.format(username))

    def user_pw(self, username, password):
        try:
            user = db.session.query(User).filter_by(name=username).one()
        except NoResultFound:
            raise ValueError('User {} does not exist'.format(username))

        user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user.time_updated = int(utils.now())
        db.session.commit()

    def group_add(self, groupname):
        try:
            group = Group(name=groupname)
            db.session.add(group)
            db.session.commit()
        except IntegrityError:
            raise ValueError('Group {} exists already'.format(groupname))

    def group_rm(self, groupname):
        try:
            group = db.session.query(Group).filter_by(name=groupname).one()
            db.session.delete(group)
            db.session.commit()
        except NoResultFound:
            raise ValueError('Group {} does not exist'.format(groupname))

    def group_adduser(self, groupname, username):
        try:
            group = db.session.query(Group).filter_by(name=groupname).one()
        except NoResultFound:
            raise ValueError('Group {} does not exist'.format(groupname))
        try:
            user = db.session.query(User).filter_by(name=username).one()
        except NoResultFound:
            raise ValueError('User {} does not exist'.format(username))
        group.users.append(user)
        db.session.commit()

    def group_rmuser(self, groupname, username):
        try:
            group = db.session.query(Group).filter_by(name=groupname).one()
        except NoResultFound:
            raise ValueError('Group {} does not exist'.format(groupname))
        try:
            user = db.session.query(User).filter_by(name=username).one()
        except NoResultFound:
            raise ValueError('User {} does not exist'.format(username))
        if user in group.users:
            group.users.remove(user)
        db.session.commit()

    def check_authorization(self, acl, authorization):
        username = None
        groups = {'__unauthenticated__'}
        if authorization:
            try:
                token = authorization.replace('Bearer ', '')
                session = jwt.decode(token, current_app.config['SECRET_KEY'])
                user = db.session.query(User).filter_by(name=session['sub']).one()
            except:
                flask.abort(401)
            if user.time_updated > session['iat']:
                flask.abort(401)
            username = user.name
            groups = set([g.name for g in user.groups])
            groups.add('__authenticated__')

        elif '__unauthenticated__' not in acl:
            flask.abort(401)

        if acl and not len(acl.intersection(groups)):
            flask.abort(403)

        flask.request.username = username
        flask.request.user_groups = groups


@marv_api_group()
def auth(app):
    assert not hasattr(app, 'um')  # TODO: correct place for extension
    app.um = UserManager()


def generate_token(username):
    now = int(time.time())
    return jwt.encode({
        'exp': now + 2419200, # 4 weeks expiration
        'iat': now,
        'sub': username,
    }, current_app.config['SECRET_KEY'])


@auth.endpoint('/auth', methods=['POST'], force_acl=['__unauthenticated__'])
def auth_post():
    req = flask.request.get_json()
    if not req:
        flask.abort(400)
    username = req.get('username', '')
    password = req.get('password', '').encode('utf-8')

    if not current_app.um.authenticate(username, password):
        return flask.abort(422)

    return flask.jsonify({'access_token': generate_token(username)})
