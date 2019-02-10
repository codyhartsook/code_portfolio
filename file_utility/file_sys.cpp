// $Id: file_sys.cpp,v 1.6 2018-06-27 14:44:57-07 - - $

// main data stucture
// tree of nodes which are either files or directories

#include <iostream>
#include <stdexcept>
#include <unordered_map>

using namespace std;

#include "debug.h"
#include "file_sys.h"

int inode::next_inode_nr {1}; 

struct file_type_hash { 
   size_t operator() (file_type type) const {
      return static_cast<size_t> (type);
   }
};

ostream& operator<< (ostream& out, file_type type) {
   static unordered_map<file_type,string,file_type_hash> hash {
      {file_type::PLAIN_TYPE, "PLAIN_TYPE"},
      {file_type::DIRECTORY_TYPE, "DIRECTORY_TYPE"},
   };
   return out << hash[type];
}

/////////////////////////////////////////////////////////////////
// constructors
/////////////////////////////////////////////////////////////////

inode_state::inode_state() {
   DEBUGF ('i', "root = " << root << ", cwd = " << cwd
          << ", prompt = \"" << prompt() << "\"");
   
   string root_title = "/";
   inode Root(file_type::DIRECTORY_TYPE);
   this->root = Root.contents;
   this->root->set_parent(nullptr);
   this->root->title = root_title;
   this->root->my_num = 1;

   this->cwd = this->root; // cwd is originallly set to root
   //cout << "created root and cwd" << endl;
}

// given file_type (plain type or dir type), get a ptr to a dir or file
inode::inode(file_type type): inode_nr (next_inode_nr++) { 
   switch (type) {
      case file_type::PLAIN_TYPE:
           contents = make_shared<plain_file>();
           break;
      case file_type::DIRECTORY_TYPE: 
           contents = make_shared<directory>(); 
           break;
   }
   DEBUGF ('i', "inode " << inode_nr << ", type = " << type);
}

/////////////////////////////////////////////////////////////////
// access functions
/////////////////////////////////////////////////////////////////

base_file_ptr inode_state::get_root() {
   return this->root;
}

base_file_ptr inode_state::get_cwd() {
   return this->cwd;
}

base_file_ptr plain_file::get_parent() {
   return this->parent;
}

base_file_ptr directory::get_parent() {
   return this->parent;
}

map<string,base_file_ptr> plain_file::get_dirents() {
   //cout << "error in getting dirents" << endl;
   throw file_error ("is a plain file");
}

map<string,base_file_ptr> directory::get_dirents() {
   return this->dirents;
}

// ------------------------------------------------------------------
void plain_file::set_parent(base_file_ptr par) {
   this->parent = par;
}

// ------------------------------------------------------------------
void directory::set_parent(base_file_ptr par) {
   this->parent = par;
}

// set the cwd to new path ------------------------------------------
void inode_state::set_cwd(base_file_ptr path) {
   this->cwd = path;
   //this->cwd->parent
}

// get a base_file_ptr ----------------------------------------------
base_file_ptr inode::get_basefile_ptr() {
   return this->contents;
}

bool plain_file::get_file_type() {
   return this->isdir;
}

bool directory::get_file_type() {
   return this->isdir;
}

const string& inode_state::prompt() const { return prompt_; }

ostream& operator<< (ostream& out, const inode_state& state) {
   out << "inode_state: root = " << state.root
       << ", cwd = " << state.cwd;
   return out;
}

// ------------------------------------------------------------------
int inode::get_inode_nr() const { // incomplete
   DEBUGF ('i', "inode = " << inode_nr);
   return inode_nr;
}

// ------------------------------------------------------------------
size_t plain_file::size() const { // incomplete
   // how many chars in file
   size_t size {0};
   DEBUGF ('i', "size = " << size);
   // chars in data vector
   string total;
   for (unsigned int i=0; i<this->data.size(); i++){
      total += this->data[i]+" ";
   }
   if (this->data.size() == 0){
      size = total.length();
   }
   else{
      size = total.length()-1;
   }
   return size;
}

// ------------------------------------------------------------------
size_t directory::size() const {
   size_t size {0};
   DEBUGF ('i', "size = " << size);
   // elements in map
   size = this->dirents.size()+2; // +2 for cwd and parent
   return size;
}

// ------------------------------------------------------------------
void plain_file::print_contents() {
   throw file_error ("is a plain file");
}

// ------------------------------------------------------------------
void directory::print_contents() {
   // print all keys in this->map
   // if this is a file, dont look for map
   try{
      //cout << "in print contents" << endl;
      this->get_dirents();
   } catch (file_error){
      cout << "error in print_contents: file_error" << endl;
   }

   for (auto i=this->dirents.begin(); i!=dirents.end(); i++){
      cout << "     ";
      cout << i->second->my_num; // basefile number
      if (i->second->size() < 10){
         cout << "     ";
      }
      else if (i->second->size() < 100){
         cout << "    ";
      }
      else if (i->second->size() < 1000){
         cout << "   ";
      }
      //cout << "#  "; // size
      cout << i->second->size() << "  ";
      if (i->second->get_file_type() == true){
         cout << i->first+"/" << endl;
      }
      else{
      cout << i->first << endl; // basefile name
      }
   }
}

/////////////////////////////////////////////////////////////////
// manipulation functions
/////////////////////////////////////////////////////////////////


// ------------------------------------------------------------------
file_error::file_error (const string& what): // complete
            runtime_error (what) {
}

// ------------------------------------------------------------------
const wordvec& plain_file::readfile() const { // incomplete
   // read from this file
   DEBUGF ('i', data);
   for (unsigned int i=0; i<this->data.size(); i++){
      cout << this->data[i]+" ";
   }
   cout << endl;

   return this->data;
}

// ------------------------------------------------------------------
const wordvec& directory::readfile() const { // complete
   throw file_error ("is a directory");
}

// ------------------------------------------------------------------
void plain_file::writefile (const wordvec& words) { // incomplete
   DEBUGF ('i', words);
   // write these words to file
   for (unsigned int i=2; i<words.size(); i++){
      
      this->data.push_back(words.at(i));
   }

}

// ------------------------------------------------------------------
void directory::writefile (const wordvec&) { // complete
   throw file_error ("is a directory");
}

// ------------------------------------------------------------------
void plain_file::remove (const string&) { // not a file or dir
   throw file_error ("is a plain file");
}

int plain_file::disown (const string&) {
   throw file_error ("is a plain file");
}

int directory::disown (const string& key) {
   int num = this->dirents.erase(key);
   return num;
}

// ------------------------------------------------------------------
void directory::remove (const string& filename) { // incomplete
   DEBUGF ('i', filename);

   base_file_ptr found = r_find(filename); // search key
   
   // check for empty directory
   if (found != nullptr and found->get_file_type() == true){ 
      
      if (found->get_dirents().size() == 0){ // is it empty
         // removing an empty directory
         base_file_ptr par = found->get_parent();
         par->disown(filename);
      }
   }
   // search for file
   else if (found != nullptr and found->get_file_type() == false){
      // removing file
      base_file_ptr par = found->get_parent();
      par->disown(filename);
   }
   else {
      throw file_error ("the specified file or directory was not found");
   }
}

// ------------------------------------------------------------------
base_file_ptr plain_file::mkdir (const string&, int) { // not a file or dir
   throw file_error ("is a plain file");
}

// ------------------------------------------------------------------
base_file_ptr plain_file::mkfile (const string&, int) { // not a file or dir
   throw file_error ("is a plain file");
}

bool plain_file::traverse(string&) {
   throw file_error ("this is a plain file");
}

bool directory::traverse(string& dir_name) {
   if (this->isdir == false){
      return false;
   }

   for (auto& x: this->get_dirents()){
      if (x.second->get_file_type() == false){
         continue;
      }
         
      cout << dir_name;
      cout << x.second->title;
         
      cout << ":" << endl; // print directory
      cout << "     " << x.second->my_num; // print its num
      if (x.second->size() < 10){
         cout << "     ";
      }
      else if (x.second->size() < 100){
         cout << "    ";
      }
      else if (x.second->size() < 1000){
         cout << "   ";
      }
      cout << x.second->size() << "  ";
      cout << "." << endl;

      // print parent info
      cout << "     " << x.second->get_parent()->my_num;
      if (x.second->get_parent()->size() < 10){
         cout << "     ";
      }
      else if (x.second->get_parent()->size() < 100){
         cout << "    ";
      }
      else if (x.second->get_parent()->size() < 1000){
         cout << "   ";
      }
      cout << x.second->get_parent()->size() << "  ";
      cout << ".." << endl;
      x.second->print_contents(); // depth first print

      if (x.second->get_dirents().size() > 0){
         if (dir_name == "/"){
            dir_name = x.second->title;
         }
         else {
            dir_name = dir_name + x.second->title;
         }
         x.second->traverse(dir_name); // recursive call
         return true;
      }
   }
   return false;
}

// ------------------------------------------------------------------
base_file_ptr plain_file::r_find(const string&) {
   throw file_error ("is a plain file");
}

// ------------------------------------------------------------------
base_file_ptr directory::r_find(const string& key) {
   string temp_key = key;

   if (this->title == key){ // ignore the fist char
      return nullptr;
   }
   else {
      for (auto& x: this->get_dirents()){
         if (x.first == temp_key){
            return x.second;
         }
         if (x.second->get_file_type() == false){ // this is a file not dir
            continue;
         }
         else if (x.second->get_dirents().size() > 0){ // was else if
            base_file_ptr result = x.second->r_find(key);
            if (result != nullptr){
               return result;
            }
         }
      }
   }
   return nullptr;
}


base_file_ptr plain_file::find_file(const string& file1){
   for (auto& x: this->get_dirents()){
      if (x.first == file1){
         return x.second;
      }
   }
   return nullptr;
}

base_file_ptr directory::find_file(const string& file1){
for (auto& x: this->get_dirents()){
      if (x.first == file1){
         return x.second;
      }
   }
   return nullptr;
}

// ------------------------------------------------------------------
base_file_ptr directory::mkdir (const string& dirname, int my_num) { 
   DEBUGF ('i', dirname);
   
   string temp_name = dirname;
   inode dir(file_type::DIRECTORY_TYPE); // get a base_file_ptr
   this->dirents.emplace(dirname, dir.contents); // insert in map
   dir.contents->title = "/"+temp_name; // set title name for new dir
   dir.contents->my_num = my_num;

   return dir.contents;
}

// ------------------------------------------------------------------
base_file_ptr directory::mkfile (const string& filename, int my_num) { 
   DEBUGF ('i', filename);
   
   inode file(file_type::PLAIN_TYPE);
   this->dirents.emplace(filename, file.contents);
   file.contents->title = filename;
   file.contents->my_num = my_num;
   
   return file.contents; // returns files base_file_ptr
}








