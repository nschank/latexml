# import re

# COMMENT_PATERN = re.compile("([^\\\\])%.*($)", flags=re.MULTILINE)
# REDACT = "%"
# COMMENT_REPLACE = "\\1{}\\2".format(REDACT)
# def strip_comments(document_contents):
#   return COMMENT_PATERN.sub(COMMENT_REPLACE, document_contents)

import strip_comments

def strip_latex_comments(document_contents):
    return strip_comments.strip_comments(document_contents)

test1in = """% Some comment
% Comment w/ escaped percent sign: \%
%%% Comment starting w/ multiple percents
Here's some math: $3 + 3 = 6$ % and here's a comment
% Yes.
Look a percent sign: \\%. Isn't it great?
Hard newline then comment: \\\\%this is a comment.
% p break:

\\begin{verbatim}%
% Unescaped % percent % signs are allowed here.
As are backslashes and such \\%\\\\%%% Hello. %
\\end{verbatim}% This is a line comment.

We want to keep comment env in its entirety:
\\begin{comment}% This should stay
This is inside the comment environment.
    It (\\%) should stay.\\\\ % So should I.
\\end{comment} This should leave.
%"""

test1out = """Here's some math: $3 + 3 = 6$ 
Look a percent sign: \\%. Isn't it great?
Hard newline then comment: \\\\

\\begin{verbatim}%
% Unescaped % percent % signs are allowed here.
As are backslashes and such \\%\\\\%%% Hello. %
\\end{verbatim}

We want to keep comment env in its entirety:
\\begin{comment}% This should stay
This is inside the comment environment.
    It (\\%) should stay.\\\\ % So should I.
\\end{comment}
"""

def strip_latex_comments_test():
    return strip_latex_comments(test1in) == test1out

def main():
    passed = strip_latex_comments_test()
    print "Test {}".format("passed" if passed  else "failed")

foo = """%W
X% p break:

Y%hello
\\begin{verbatim}
blah
\\end{verbatim}
"""
def debug_foo():
    print "------------------------------- OLD --------------------------------"
    print foo
    print "------------------------------- ... --------------------------------"
    out = strip_latex_comments(foo)
    print "------------------------------- NEW --------------------------------"
    print out

def debug_big_test():
    print "------------------------------- OLD --------------------------------"
    print test1in
    print "------------------------------- ... --------------------------------"
    out = strip_latex_comments(test1in)
    print "------------------------------- NEW --------------------------------"
    print out
    print "------------------------------- EXP --------------------------------"
    print test1out
    print "--------------------------------------------------------------------"

if __name__ == '__main__':
    # debug_foo()
    # debug_big_test()
    main()  
