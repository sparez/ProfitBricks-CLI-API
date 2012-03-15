#!/usr/bin/python

#
# Copyright 2012 ProfitBricks GmbH
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

import sys
import logging
logging.basicConfig(level=logging.INFO)

import pb.api
import pb.formatter
import pb.argsparser
import pb.helper

## Parse arguments

argsParser = pb.argsparser.ArgsParser()
argsParser.readUserArgs()

# Make sure we have an operation

requestedOp = argsParser.getRequestedOperation()
if requestedOp is None:
	print sys.argv
	print "Unknown operation:", argsParser.baseArgs["op"]
	sys.exit(2)

# @ operations don't require pb api nor authentication

if requestedOp[0] == "@":
	helper = pb.helper.Helper()
	pb.argsparser.ArgsParser.operations[requestedOp]["lambda"](helper)
	sys.exit(0)

# perform regular (non-@) operation

if not argsParser.isAuthenticated():
	pb.errorhandler.ArgsError("Missing authentication")

formatter = pb.formatter.Formatter()
if argsParser.baseArgs["s"]:
	formatter.shortFormat()

api = pb.api.API(argsParser.baseArgs["u"], argsParser.baseArgs["p"], debug = argsParser.baseArgs["debug"])

pb.argsparser.ArgsParser.operations[requestedOp]["lambda"](formatter, api, argsParser.opArgs)
if not argsParser.baseArgs["s"]:
	print ""
	print "Request ID:", str(api.requestId) if api.requestId is not None else "(none)"

