# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
import imaplib

from collections import namedtuple

logger = logging.getLogger(__name__)


class IMAPAuthProvider:
    def __init__(self, config, account_handler):
        self.account_handler = account_handler
        self.create_users = config.create_users
        self.server = config.server
        self.port = config.port
        self.plain_uid = config.plain_userid
        self.append_domain = config.append_domain

    async def check_password(self, user_id, password):
        """ Attempt to authenticate a user against IMAP
            and register an account if none exists.

            Returns:
                True if authentication against IMAP was successful
        """

        if not user_id or not password:
            return None

        localpart = user_id.split(":", 1)[0][1:]
        email = '@'.join(user_id[1:].split(':'))

        if self.plain_uid:
            address = localpart
        else:
            # user_id is of the form @foo:bar.com
            address = email

        return await self.check_3pid_auth("email", address, password, user_id=user_id, localpart=localpart)

    async def check_3pid_auth(self, medium, address, password, user_id=None, localpart=None):
        """ Handle authentication against third-party login types, such as email
            Args:
                medium (str): Medium of the 3PID (e.g email, msisdn).
                address (str): Address of the 3PID (e.g bob@example.com for email).
                password (str): The provided password of the user.
            Returns:
                user_id (str|None): ID of the user if authentication
                    successful. None otherwise.
        """

        if not address or not password:
            return None

        # We support only email
        if medium != "email":
            return None

        logger.debug("Trying to login as {} on {}:{} via IMAP".format(address, self.server, self.port))

        try:
            M = imaplib.IMAP4_SSL(self.server, self.port)
            r = M.login(address, password)
            if r[0] == 'OK':
                M.logout()
        except imaplib.IMAP4.error as e:
            logger.debug("IMAP exception occurred: {}".format(str(e)))
            return None

        if r[0] != 'OK':
            logger.debug("IMAP login failed for {}".format(address))
            return None

        # Guessing localpart
        if not localpart:
            # Trimming domain and what's after '+'
            localpart = address.split("@")[0].split("+")[0]
            logger.debug("Guessed localpart for {}: {}".format(address, localpart))

        # Need to find user_id
        if not user_id:
            if self.append_domain:
                domain = self.append_domain
            else:
                # Guessing domain given email domain
                if '@' in address:
                    domain = address.split('@')[-1]
                else:
                    logger.debug("No domain can be guessed for {}".format(address))
                    return None

            logger.debug("Guessed domain for {}: {}".format(address, domain))

            user_id = "@{}:{}".format(localpart, domain)

        logger.debug("IMAP login successful, checking whether user_id {} exists in Matrix".format(user_id))

        if await self.account_handler.check_user_exists(user_id):
            logger.debug("{} exists in our database; login successful for {}!".format(user_id, address))
            return user_id

        logger.debug("{} was not found in Matrix".format(user_id))

        # Otherwise, attempt to create the user in Matrix if required
        if not self.create_users:
            return None

        # We need to have a valid email address for registration
        if '@' in address:
            email = address
        else:
            # Building the email address if `address` was not a valid email
            email = '@'.join(user_id[1:].split(':'))

        logger.debug("Attempting to create user {} with email {}".format(user_id, address))

        # Create the user in Matrix
        user_id, access_token = await self.account_handler.register(localpart=localpart, emails=[email])

        logging.info("User {} successfully created!".format(user_id))

        return user_id

    @staticmethod
    def parse_config(config):
        imap_config = namedtuple('_Config', 'create_users')
        imap_config.enabled = config.get('enabled', False)
        imap_config.create_users = config.get('create_users', True)
        imap_config.server = config.get('server', '')
        imap_config.port = config.get('port', imaplib.IMAP4_SSL_PORT)
        imap_config.plain_userid = config.get('plain_userid', False)
        imap_config.append_domain = config.get('append_domain', '')
        return imap_config
