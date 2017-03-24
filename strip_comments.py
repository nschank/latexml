# Stolen & adapted from gist.github.com/amerberg/a273ca1e579ab573b499
# Retrieved 2017-03-24

import ply.lex, argparse, io

#Usage
# python stripcomments.py input.tex > output.tex
# python stripcomments.py input.tex -e encoding > output.tex

def strip_comments(source):
    tokens = (
                'PERCENT', 'BEGINCOMMENT', 'ENDCOMMENT', 'BACKSLASH',
                'CHAR', 'BEGINVERBATIM', 'ENDVERBATIM', 'NEWLINE', 'ESCPCT',
                'PERCENTONLY'
             )
    states = (
                ('linecomment', 'exclusive'),
                ('linecommentonly', 'exclusive'),
                ('commentenv', 'exclusive'), 
                ('verbatim', 'exclusive')
            )
    
    #Deal with escaped backslashes, so we don't think they're escaping %.
    def t_ANY_BACKSLASH(t):
        r"\\\\"
        return t

    #Lines that only have a comment
    def t_PERCENTONLY(t):
        r'(?m)^\s*\%'
        t.lexer.begin("linecommentonly")

    #One-line comments
    def t_PERCENT(t):
        r"\%"
        t.lexer.begin("linecomment")
     
    #Escaped percent signs
    def t_ESCPCT(t):
        r"\\\%"
        return t
    
    #Comment environment, as defined by verbatim package       
    def t_BEGINCOMMENT(t):
        r"\\begin\s*{\s*comment\s*}"
        t.lexer.begin("commentenv")
        return t
    
    #Verbatim environment (different treatment of comments within)   
    def t_BEGINVERBATIM(t):
        r"\\begin\s*{\s*verbatim\s*}"
        t.lexer.begin("verbatim")
        return t
    
    #Any other character in initial state we leave alone    
    def t_CHAR(t):
        r"."
        return t
        
    def t_NEWLINE(t):
        r"\n"
        return t
    
    #End comment environment    
    def t_commentenv_ENDCOMMENT(t):
        r"\\end\s*{\s*comment\s*}"
        #Anything after \end{comment} on a line is ignored!
        t.lexer.begin('linecomment')
        return t
    
    #Ignore comments of comment environment    
    def t_commentenv_CHAR(t):
        r"."
        return t
        pass
        
    def t_commentenv_NEWLINE(t):
        r"\n"
        return t
        pass
    
    #End of verbatim environment    
    def t_verbatim_ENDVERBATIM(t):
        r"\\end\s*{\s*verbatim\s*}"
        t.lexer.begin('INITIAL')
        return t
        
    #Leave contents of verbatim environment alone
    def t_verbatim_CHAR(t):
        r"."
        return t
        
    def t_verbatim_NEWLINE(t):
        r"\n"
        return t
    
    #End a % comment when we get to a new line
    def t_linecomment_ENDCOMMENT(t):
        r"\n"
        t.lexer.begin("INITIAL")
        return t # keep newline in this case
    
    #Ignore anything after a % on a line        
    def t_linecomment_CHAR(t):
        r"."
        pass

    #Ignore anything after a % on a line        
    def t_linecommentonly_CHAR(t):
        r"."
        pass

    #End a % comment when we get to a new line
    def t_linecommentonly_ENDCOMMENT(t):
        r"\n"
        t.lexer.begin("INITIAL")
        #Newline at the end of a linecommentonly is stripped.

    def generic_error(t):
        err = """
        Could not parse LaTeX: Unexpected token {}".format(str(t.value[0]))
        """
        raise err

    def t_error(t):
        return generic_error(t)

    def t_commentenv_error(t):
        return generic_error(t)

    def t_linecomment_error(t):
        return generic_error(t)

    def t_linecommentonly_error(t):
        return generic_error(t)

    def t_verbatim_error(t):
        return generic_error(t)
        
    lexer = ply.lex.lex()

    lexer.input(source)
    # print [tok for tok in lexer]
    return u"".join([tok.value for tok in lexer])
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help = 'the file to strip comments from')
    parser.add_argument('--encoding', '-e', default='utf-8')
    
    args = parser.parse_args()
    
    with io.open(args.filename, encoding=args.encoding) as f:
        source = f.read()
    
    print(strip_comments(source))
    
if __name__ == '__main__':
    main()