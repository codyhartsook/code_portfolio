// $Id: file_sys.h,v 1.6 2018-06-27 14:44:57-07 - - $
// header file for file_sys.cpp

#ifndef __INODE_H__
#define __INODE_H__

#include <exception>
#include <iostream>
#include <memory>
#include <map>
#include <vector>
using namespace std;

#include "util.h"


// inode_t -
// An inode is either a directory or a plain file.

/////////////////////////////////////////////////////////////////
// file_type enum class
/////////////////////////////////////////////////////////////////

enum class file_type {PLAIN_TYPE, DIRECTORY_TYPE};
class inode;
class base_file;
class plain_file;
class directory;
using inode_ptr = shared_ptr<inode>;
using base_file_ptr = shared_ptr<base_file>;
ostream& operator<< (ostream&, file_type);


/////////////////////////////////////////////////////////////////
// inode_state class
/////////////////////////////////////////////////////////////////

// inode_state -
//    A small convenient class to maintain the state of the simulated
//    process:  the root (/), the current directory (.), and the
//    prompt.

class inode_state {
   friend class inode;
   friend ostream& operator<< (ostream& out, const inode_state&);
   private:
      //inode_ptr root {nullptr};
      //inode_ptr cwd {nullptr};
      base_file_ptr root;
      base_file_ptr cwd;
   public:
      inode_state (const inode_state&) = delete; // copy ctor
      inode_state& operator= (const inode_state&) = delete; // op=
      inode_state();
      base_file_ptr get_cwd();
      base_file_ptr get_root();
      void set_cwd(base_file_ptr path);
      const string& prompt() const;
      string prompt_ {"% "}; 
      int tree_num = 1;
};

/////////////////////////////////////////////////////////////////
// inode class
/////////////////////////////////////////////////////////////////

// class inode -
// inode ctor -
//    Create a new inode of the given type.
// get_inode_nr -
//    Retrieves the serial number of the inode.  Inode numbers are
//    allocated in sequence by small integer.
// size -
//    Returns the size of an inode.  For a directory, this is the
//    number of dirents.  For a text file, the number of characters
//    when printed (the sum of the lengths of each word, plus the
//    number of words.
//    

class inode {
   friend class inode_state;
   friend class base_file;
   private:
      static int next_inode_nr;
      int inode_nr;
   public:
      base_file_ptr contents;
      const string title;
      base_file_ptr parent;
      inode (file_type);
      int get_inode_nr() const;
      base_file_ptr get_basefile_ptr();
};


// class base_file -
// Just a base class at which an inode can point.  No data or
// functions.  Makes the synthesized members useable only from
// the derived classes.

class file_error: public runtime_error {
   public:
      explicit file_error (const string& what);
};


/////////////////////////////////////////////////////////////////
// base_file class
/////////////////////////////////////////////////////////////////

class base_file {
   protected:
      base_file() = default;
   public:
      virtual ~base_file() = default;
      base_file (const base_file&) = delete;
      base_file& operator= (const base_file&) = delete;
      virtual size_t size() const = 0;
      virtual const wordvec& readfile() const = 0;
      virtual void writefile (const wordvec& newdata) = 0;
      virtual base_file_ptr find_file(const string& file1) = 0;
      virtual void remove (const string& filename) = 0;
      virtual base_file_ptr mkdir (const string& dname,int my_num) =0;
      virtual base_file_ptr mkfile (const string& fname,int my_num) =0;
      virtual void print_contents() = 0;
      virtual base_file_ptr r_find(const string& path) = 0;
      virtual base_file_ptr get_parent() = 0;
      virtual void set_parent(base_file_ptr par) = 0;
      virtual map<string,base_file_ptr> get_dirents() = 0;
      virtual bool traverse(string& dir_name) = 0;
      virtual bool get_file_type() = 0;
      virtual int disown(const string& key) = 0;
      string title;
      int my_num;
};

/////////////////////////////////////////////////////////////////
// plain_file class
/////////////////////////////////////////////////////////////////

// Used to hold data.
// synthesized default ctor -
//    Default vector<string> is a an empty vector.
// readfile -
//    Returns a copy of the contents of the wordvec in the file.
// writefile -
//    Replaces the contents of a file with new contents.

class plain_file: public base_file {
   private:
      wordvec data;
      base_file_ptr parent;
      bool isdir = false;
   public:
      virtual size_t size() const override;
      virtual const wordvec& readfile() const override;
      virtual void writefile (const wordvec& newdata) override;
      virtual base_file_ptr find_file(const string&) override;
      virtual void remove (const string& filename) override;
      virtual base_file_ptr mkdir (const string& dname, int my_num) override;
      virtual base_file_ptr mkfile (const string& fname, int my_num) override;
      virtual void print_contents() override;
      virtual base_file_ptr r_find(const string& path) override;
      virtual base_file_ptr get_parent() override;
      virtual void set_parent(base_file_ptr par) override;
      virtual map<string,base_file_ptr> get_dirents() override;
      virtual bool traverse(string& dir_name) override;
      virtual bool get_file_type() override;
      virtual int disown(const string& key) override;
      int my_num;

};

/////////////////////////////////////////////////////////////////
// directory class
/////////////////////////////////////////////////////////////////

// Used to map filenames onto inode pointers.
// default ctor -
//    Creates a new map with keys "." and "..".
// remove -
//    Removes the file or subdirectory from the current inode.
//    Throws an file_error if this is not a directory, the file
//    does not exist, or the subdirectory is not empty.
//    Here empty means the only entries are dot (.) and dotdot (..).
// mkdir -
//    Creates a new directory under the current directory and 
//    immediately adds the directories dot (.) and dotdot (..) to it.
//    Note that the parent (..) of / is / itself.  It is an error
//    if the entry already exists.
// mkfile -
//    Create a new empty text file with the given name.  Error if
//    a dirent with that name exists.

class directory: public base_file {
   private:
      // Must be a map, not unordered_map, so printing is lexicographic
      map<string,base_file_ptr> dirents;
      base_file_ptr parent;
       bool isdir = true;

   public:
      virtual size_t size() const override;
      virtual const wordvec& readfile() const override;
      virtual void writefile (const wordvec& newdata) override;
      virtual base_file_ptr find_file(const string&) override;
      virtual void remove (const string& filename) override;
      virtual base_file_ptr mkdir (const string& dname, int my_num) override;
      virtual base_file_ptr mkfile (const string& fname, int my_num) override;
      virtual void print_contents() override;
      virtual base_file_ptr r_find(const string& path) override;
      virtual base_file_ptr get_parent() override;
      virtual void set_parent(base_file_ptr par) override;
      virtual map<string,base_file_ptr> get_dirents() override;
      virtual bool traverse(string& dir_name) override;
      virtual bool get_file_type() override;
      virtual int disown(const string& key) override;
      int my_num;
};

#endif

