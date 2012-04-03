#include <newparser.h>
#include <lexer.h>

const ParseTree* ParseTree::
get_branch(const std::string& name) const
{
    std::map<std::string,ParseTree>::const_iterator p=branches.find(name);
    if(p==branches.end()) return 0;
    else return &p->second;
}

bool ParseTree::remove_first_matching_branch( const std::string& name )
{
    std::map<std::string,ParseTree>::iterator p=branches.find(name);
    if(p==branches.end()) return false;
    branches.erase( p );
    return true;
}

bool ParseTree::
get_number(const std::string& name, double& result) const
{
    std::map<std::string,double>::const_iterator p=numbers.find(name);
    if(p==numbers.end()) return false;
    result=p->second;
    return true;
}

bool ParseTree::
get_int(const std::string& name, int& result) const
{
    double number;
    if(get_number(name, number)){
        result=(int)std::floor(number);
        return true;
    }else
        return false;
}

bool ParseTree::
get_string(const std::string& name, std::string& result) const
{
    std::map<std::string,std::string>::const_iterator p=strings.find(name);
    if(p==strings.end()) return false;
    result=p->second;
    return true;
}

const Array1d* ParseTree::
get_vector(const std::string& name) const
{
    std::map<std::string,Array1d>::const_iterator p=vectors.find(name);
    if(p==vectors.end()) return 0;
    else return &p->second;
}

bool ParseTree::
get_vec2d(const std::string& name, Vec2d& v) const
{
    std::map<std::string,Array1d>::const_iterator p=vectors.find(name);
    if(p==vectors.end()) return false;
    if(p->second.n!=2){
        std::cerr<<"Error: looking for 2d vector ["<<name<<"] but got dimension "<<p->second.n<<std::endl;
        return false;
    }
    v[0]=p->second[0];
    v[1]=p->second[1];
    return true;
}

bool ParseTree::
get_vec3d(const std::string& name, Vec3d& v) const
{
    std::map<std::string,Array1d>::const_iterator p=vectors.find(name);
    if(p==vectors.end()) return false;
    if(p->second.n!=3){
        std::cerr<<"Error: looking for 3d vector ["<<name<<"] but got dimension "<<p->second.n<<std::endl;
        return false;
    }
    v[0]=p->second[0];
    v[1]=p->second[1];
    v[2]=p->second[2];
    return true;
}

namespace {
    
    bool parse_vector(Lexer& lexer, Array1d& v)
    {
        Token token;
        v.resize(0);
        for(;;){
            lexer.read(token);
            switch(token.type){
                case TOKEN_EOF:
                    std::cerr<<"Parse error: looking for closing bracket but hit end-of-file"<<std::endl;
                    return false;
                case TOKEN_ERROR:
                    std::cerr<<"Lex error: cannot make sense of ["<<token.string_value<<"]"<<std::endl;
                    return false;
                case TOKEN_NUMBER:
                    v.push_back(token.number_value);
                    break;
                case TOKEN_RIGHT_BRACKET:
                    return true;
                default:
                    std::cerr<<"Parse error: looking for a number or a closing bracket, got unexpected token "<<token<<std::endl;
                    return false;
            }
        }
    }
    
    bool recursive_parse(Lexer& lexer, ParseTree& tree, bool root_level)
    {
        Token token;
        std::string name;
        for(;;){
            lexer.read(token);
            switch(token.type){
                case TOKEN_EOF:
                    if(!root_level){
                        std::cerr<<"Parse error: looking for closing parenthesis but hit end-of-file"<<std::endl;
                        return false;
                    }else
                        return true;
                case TOKEN_ERROR:
                    std::cerr<<"Lex error: cannot make sense of ["<<token.string_value<<"]"<<std::endl;
                    return false;
                case TOKEN_IDENTIFIER: case TOKEN_STRING:
                    name=token.string_value;
                    if(tree.branches.find(name)!=tree.branches.end()
                       || tree.numbers.find(name)!=tree.numbers.end()
                       || tree.strings.find(name)!=tree.strings.end()
                       || tree.vectors.find(name)!=tree.vectors.end()){
                        std::cerr<<"Parse error: name ["<<name<<"] appears multiple times in record"<<std::endl;
                        return false;
                    }
                    break;
                case TOKEN_RIGHT_PAREN:
                    if(root_level){
                        std::cerr<<"Parse error: hit closing parenthesis at root level"<<std::endl;
                        return false;
                    }else
                        return true;
                default:
                    std::cerr<<"Parse error: looking for a name, got unexpected token "<<token<<std::endl;
                    return false;
            }
            // we've now got the name, let's read the value
            lexer.read(token);
            switch(token.type){
                case TOKEN_EOF:
                    std::cerr<<"Parse error: looking for a value for ["<<name<<"] but hit end-of-file"<<std::endl;
                    return false;
                case TOKEN_ERROR:
                    std::cerr<<"Lex error: cannot make sense of ["<<token.string_value<<"]"<<std::endl;
                    return false;
                case TOKEN_IDENTIFIER: case TOKEN_STRING:
                    tree.strings.insert(std::make_pair(name, token.string_value));
                    break;
                case TOKEN_NUMBER:
                    tree.numbers.insert(std::make_pair(name, token.number_value));
                    break;
                case TOKEN_LEFT_PAREN:
                {
                    ParseTree subtree;
                    if(!recursive_parse(lexer, subtree, false)) return false;
                    tree.branches.insert(std::make_pair(name, subtree));
                }
                    break;
                case TOKEN_RIGHT_PAREN:
                    std::cerr<<"Parse error: looking for a value for ["<<name<<"] but hit closing parenthesis"<<std::endl;
                    return false;
                case TOKEN_LEFT_BRACKET:
                {
                    Array1d v;
                    if(!parse_vector(lexer, v)) return false;
                    tree.vectors.insert(std::make_pair(name, v));
                }
                    break;
                case TOKEN_RIGHT_BRACKET:
                    std::cerr<<"Parse error: looking for a value for ["<<name<<"] but hit closing bracket"<<std::endl;
                    return false;
            }
        }
    }
    
}  // unnamed namespace


bool parse_stream(std::istream& input, ParseTree& tree)
{
    Lexer lexer(input);
    return recursive_parse(lexer, tree, true);
}
