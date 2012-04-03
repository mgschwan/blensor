#include <lexer.h>
#include <cstdio>

Token::
Token(const Token &source) :
type(source.type),
number_value( source.number_value ),
string_value( source.string_value )
{
}

Token &Token::
operator=(const Token &source)
{
    number_value=source.number_value;
    string_value=source.string_value;
    return *this;
}

void Token::
set(TokenType type_)
{
    type=type_;
    number_value=0;
    string_value.clear();
}

void Token::
set(TokenType type_, const std::string &value)
{
    clear();
    type=type_;
    string_value=value;
}

void Token::
set(TokenType type_, double value)
{
    clear();
    type=type_;
    number_value=value;
}

void Token::
clear()
{
    string_value.clear();
}

std::ostream& operator<<(std::ostream& out, const Token& t)
{
    switch(t.type){
        case TOKEN_EOF:           out<<"EOF"; break;
        case TOKEN_ERROR:         out<<"ERROR("<<t.string_value<<")"; break;
        case TOKEN_IDENTIFIER:    out<<"ID("<<t.string_value<<")"; break;
        case TOKEN_NUMBER:        out<<"NUMBER("<<t.number_value<<")"; break;
        case TOKEN_STRING:        out<<"STRING("<<t.string_value<<")"; break;
        case TOKEN_LEFT_PAREN:    out<<"LEFT_PAREN"; break;
        case TOKEN_RIGHT_PAREN:   out<<"RIGHT_PAREN"; break;
        case TOKEN_LEFT_BRACKET:  out<<"LEFT_BRACKET"; break;
        case TOKEN_RIGHT_BRACKET: out<<"RIGHT_BRACKET"; break;
    }
    return out;
}

namespace {
    
    double double_of_string(const std::string &s)
    {
        double v;
        std::sscanf(s.c_str(), "%lf", &v);
        return v;
    }
    
} // namespace

void Lexer::
read(Token &tok)
{
    char c;
    enum {MODE_UNKNOWN, MODE_ERROR, MODE_MINUS, MODE_NUMBER, MODE_MANTISSA, MODE_E,
        MODE_EMINUS, MODE_EXPONENT, MODE_IDENTIFIER, MODE_STRING, MODE_STRINGESCAPE} mode=MODE_UNKNOWN;
    std::string token_string;
    
    for(;;){
        input.get(c);
        if(input.eof() || !input.good()){ // on end of input ////////////////////////////////////////////
            switch(mode){
                case MODE_UNKNOWN:
                    tok.set(TOKEN_EOF); return;
                case MODE_ERROR: case MODE_MINUS: case MODE_E: case MODE_EMINUS: case MODE_STRING: case MODE_STRINGESCAPE:
                    tok.set(TOKEN_ERROR, token_string); return;
                case MODE_NUMBER: case MODE_MANTISSA: case MODE_EXPONENT:
                    tok.set(TOKEN_NUMBER, double_of_string(token_string)); return;
                case MODE_IDENTIFIER:
                    tok.set(TOKEN_IDENTIFIER, token_string); return;
            }
        }else{
            switch(c){ // on a good character ///////////////////////////////////////
                case '-':
                    token_string.push_back(c);
                    switch(mode){
                        case MODE_UNKNOWN:
                            mode=MODE_MINUS;
                            break;
                        case MODE_IDENTIFIER: case MODE_STRING:
                            break;
                        case MODE_STRINGESCAPE:
                            mode=MODE_STRING;
                            break;
                        case MODE_E:
                            mode=MODE_EMINUS;
                            break;
                        default:
                            mode=MODE_ERROR;
                            break;
                    }
                    break;
                    
                case '0': case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8': case '9':
                    token_string.push_back(c);
                    switch(mode){
                        case MODE_UNKNOWN: case MODE_MINUS:
                            mode=MODE_NUMBER;
                            break;
                        case MODE_E: case MODE_EMINUS:
                            mode=MODE_EXPONENT;
                            break;
                        case MODE_STRINGESCAPE:
                            mode=MODE_STRING;
                            break;
                        default:
                            break;
                    }
                    break;
                    
                case '.':
                    token_string.push_back(c);
                    switch(mode){
                        case MODE_UNKNOWN: case MODE_NUMBER: case MODE_MINUS:
                            mode=MODE_MANTISSA;
                            break;
                        case MODE_IDENTIFIER: case MODE_STRING:
                            break;
                        case MODE_STRINGESCAPE:
                            mode=MODE_STRING;
                            break;
                        default:
                            mode=MODE_ERROR;
                    }
                    break;
                    
                case 'e': case 'E':
                    token_string.push_back(c);
                    switch(mode){
                        case MODE_NUMBER: case MODE_MANTISSA:
                            mode=MODE_E;
                            break;
                        case MODE_IDENTIFIER: case MODE_STRING:
                            break;
                        case MODE_STRINGESCAPE:
                            mode=MODE_STRING;
                            break;
                        case MODE_UNKNOWN:
                            mode=MODE_IDENTIFIER;
                            break;
                        default:
                            mode=MODE_ERROR;
                    }
                    break;
                    
                case '"': // start or end of a string
                    switch(mode){
                        case MODE_UNKNOWN:
                            mode=MODE_STRING;
                            break;
                        case MODE_STRING:
                            tok.set(TOKEN_STRING, token_string); return;
                        case MODE_STRINGESCAPE:
                            token_string.push_back(c);
                            mode=MODE_STRING;
                            break;
                        case MODE_ERROR: case MODE_MINUS: case MODE_E: case MODE_EMINUS:
                            tok.set(TOKEN_ERROR, token_string); return;
                        case MODE_NUMBER: case MODE_MANTISSA: case MODE_EXPONENT:
                            tok.set(TOKEN_NUMBER, double_of_string(token_string)); return;
                        case MODE_IDENTIFIER:
                            tok.set(TOKEN_IDENTIFIER, token_string); return;
                    }
                    break;
                    
                case '\\': // escape within a string, otherwise nothing special
                    switch(mode){
                        case MODE_UNKNOWN: case MODE_IDENTIFIER:
                            token_string.push_back(c);
                            mode=MODE_IDENTIFIER;
                            break;
                        case MODE_STRING:
                            mode=MODE_STRINGESCAPE;
                            break;
                        case MODE_STRINGESCAPE:
                            token_string.push_back(c);
                            mode=MODE_STRING;
                            break;
                        case MODE_ERROR: case MODE_MINUS: case MODE_E: case MODE_EMINUS:
                            token_string.push_back(c);
                            mode=MODE_ERROR;
                            break;
                        case MODE_NUMBER: case MODE_MANTISSA: case MODE_EXPONENT:
                            input.putback('(');
                            tok.set(TOKEN_NUMBER, double_of_string(token_string)); return;
                    }
                    break;
                    
                case ' ': case '\t': case '\r': case '\n':
                    switch(mode){
                        case MODE_UNKNOWN:
                            break; // keep going
                        case MODE_STRING:
                            token_string.push_back(c);
                            break;
                        case MODE_STRINGESCAPE:
                            token_string.push_back(c);
                            mode=MODE_STRING;
                            break;
                        case MODE_ERROR: case MODE_MINUS: case MODE_E: case MODE_EMINUS:
                            tok.set(TOKEN_ERROR, token_string); return;
                        case MODE_NUMBER: case MODE_MANTISSA: case MODE_EXPONENT:
                            tok.set(TOKEN_NUMBER, double_of_string(token_string)); return;
                        case MODE_IDENTIFIER:
                            tok.set(TOKEN_IDENTIFIER, token_string); return;
                    }
                    break;
                    
                case '#':
                    switch(mode){
                        case MODE_STRING:
                            token_string.push_back(c);
                            break;
                        case MODE_STRINGESCAPE:
                            token_string.push_back(c);
                            mode=MODE_STRING;
                            break;
                        default: // ignore the rest of the line as a comment
                            do input.get(c);
                            while(!input.eof() && input.good() && c!='\n' && c!='\r');
                    }
                    break;
                    
                case '(':
                    switch(mode){
                        case MODE_UNKNOWN:
                            tok.set(TOKEN_LEFT_PAREN); return;
                        case MODE_STRING:
                            token_string.push_back(c);
                            break;
                        case MODE_STRINGESCAPE:
                            token_string.push_back(c);
                            mode=MODE_STRING;
                            break;
                        case MODE_ERROR: case MODE_MINUS: case MODE_E: case MODE_EMINUS:
                            input.putback('(');
                            tok.set(TOKEN_ERROR, token_string); return;
                        case MODE_NUMBER: case MODE_MANTISSA: case MODE_EXPONENT:
                            input.putback('(');
                            tok.set(TOKEN_NUMBER, double_of_string(token_string)); return;
                        case MODE_IDENTIFIER:
                            input.putback('(');
                            tok.set(TOKEN_IDENTIFIER, token_string); return;
                    }
                    break;
                    
                case ')':
                    switch(mode){
                        case MODE_UNKNOWN:
                            tok.set(TOKEN_RIGHT_PAREN); return;
                        case MODE_STRING:
                            token_string.push_back(c);
                            break;
                        case MODE_STRINGESCAPE:
                            token_string.push_back(c);
                            mode=MODE_STRING;
                            break;
                        case MODE_ERROR: case MODE_MINUS: case MODE_E: case MODE_EMINUS:
                            input.putback(')');
                            tok.set(TOKEN_ERROR, token_string); return;
                        case MODE_NUMBER: case MODE_MANTISSA: case MODE_EXPONENT:
                            input.putback(')');
                            tok.set(TOKEN_NUMBER, double_of_string(token_string)); return;
                        case MODE_IDENTIFIER:
                            input.putback(')');
                            tok.set(TOKEN_IDENTIFIER, token_string); return;
                    }
                    break;
                    
                case '[':
                    switch(mode){
                        case MODE_UNKNOWN:
                            tok.set(TOKEN_LEFT_BRACKET); return;
                        case MODE_STRING:
                            token_string.push_back(c);
                            break;
                        case MODE_STRINGESCAPE:
                            token_string.push_back(c);
                            mode=MODE_STRING;
                            break;
                        case MODE_ERROR: case MODE_MINUS: case MODE_E: case MODE_EMINUS:
                            input.putback('[');
                            tok.set(TOKEN_ERROR, token_string); return;
                        case MODE_NUMBER: case MODE_MANTISSA: case MODE_EXPONENT:
                            input.putback('[');
                            tok.set(TOKEN_NUMBER, double_of_string(token_string)); return;
                        case MODE_IDENTIFIER:
                            input.putback('[');
                            tok.set(TOKEN_IDENTIFIER, token_string); return;
                    }
                    break;
                    
                case ']':
                    switch(mode){
                        case MODE_UNKNOWN:
                            tok.set(TOKEN_RIGHT_BRACKET); return;
                        case MODE_STRING:
                            token_string.push_back(c);
                            break;
                        case MODE_STRINGESCAPE:
                            token_string.push_back(c);
                            mode=MODE_STRING;
                            break;
                        case MODE_ERROR: case MODE_MINUS: case MODE_E: case MODE_EMINUS:
                            input.putback(']');
                            tok.set(TOKEN_ERROR, token_string); return;
                        case MODE_NUMBER: case MODE_MANTISSA: case MODE_EXPONENT:
                            input.putback(']');
                            tok.set(TOKEN_NUMBER, double_of_string(token_string)); return;
                        case MODE_IDENTIFIER:
                            input.putback(']');
                            tok.set(TOKEN_IDENTIFIER, token_string); return;
                    }
                    break;
                    
                default:
                    token_string.push_back(c);
                    switch(mode){
                        case MODE_UNKNOWN:
                            mode=MODE_IDENTIFIER;
                            break;
                        case MODE_IDENTIFIER: case MODE_STRING:
                            break;
                        case MODE_STRINGESCAPE:
                            mode=MODE_STRING;
                            break;
                        default:
                            mode=MODE_ERROR;
                    }
                    break;
            }
        }
    }
}

