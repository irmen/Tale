/* Everybody needs a soul, or they will wind up being called Wayne or Garth
 * Written by Profezzorn@nannymud
 * I guess I'm setting a new record in cpu-usage....
 *
 * future enhancements:
 * think <person> <feeling>
 * You think <person> <feeling>
 * (Profezzorn thinks you smile.)
 *
 * Thanks goes to Xantrax (& Mav) @ Ultraworld for the TMI-2 mudlib support.
 */

/*
Normally you shouldn't make objects that contains 'feelings' because they
should be handled by /obj/soul. If you however feel that your feelings
doesn't belong in the standard soul it is now possible to patch them into
the standard soul with the use of the following functions in the soul.

===========================================================================
NAME
	void add_verb(mapping m)

DESCRIPTION
	This function adds verbs to the soul. They will stay there until
	removed or until soul is destructed. (ie. when player log off)
	The argument m is a mapping of the same format as the one further
	down in this program as the format is quite complex I will not
	go into details here but advice you to learn from the numerous
	examples in this program.

	There is one special thing I'd like to mention though, if a verb
	is defined as a string or an object, reduce_verb will be called
	in that object instead of this object. (See reduce_verb) This
	makes it possible to go outside the normal SIMP/DEFA etc., or
	even disable certain verbs.

===========================================================================
NAME
	void remove_verb(string *v)

DESCRIPTION
	Remove_verbs removes verbs previously added to the soul, note that
	the standard verbs present from the beginning in the soul cannot
	be changed nor removed.

===========================================================================
NAME
	void add_adverb(string *v)

DESCRIPTION
	With this function you can add adverbs to the soul. It's as
	simple as that. In all other resepects it works just as add_verbs.

===========================================================================
NAME
	void remove_adverb(string *v)

DESCRIPTION
	With this function you can remove adverbs previously added.
	Note that you can not remove adverbs that are there by default.

===========================================================================
NAME
        string query_last_action()

DESCRIPTION
        This function is only valid during the call of a catch_tell()
        from this object. It returns the feeling used last
	with adverbs and persons expanded to their full names.

===========================================================================
NAME
        mixed *query_brokendown_data()

DESCRIPTION
        This call is also only valid during calls of catch_tell() from this
        object. It returns an easy-to-parse version of the command written
        on the following format:

        ({ meta-verb ,
            ({ verb ,
                ({ persons }), 
                ({ adverbs }),
                message, 
                ({ where })
            }),
            ......
        })
                  
===========================================================================
NAME
        mixed *query_feeling_for(object *who)

DESCRIPTION
        Works exactly like query_brokendown_data(), but returns
        entries used towards the object who only.

===========================================================================
        
*/


/* define this if you get eval cost too big when you try 'help adverbs'
 * with LOW_EVAL_COST, soul_adverbs _must_ be sorted in alphabetical order.
 */
/* #define LOW_EVAL_COST */

#define DEBUG 0

#ifdef __NANNYMUD__

#define HAVE_SPRINTF
#define BUGGY_EXPLODE
#define MOVE(X,Y) move_object(X,Y)
#define NAME(X) lower_case((string)(X)->query_name())
#define CAP_NAME(X) ((string)(X)->query_name())
#define ISLIVING(X) ((int)(X)->query_living())
#define ISVISIBLE(X) (!!((string)(X)->short()))
#define POSSESSIVE(X) ((string)(X)->query_possessive())
#define OBJECTIVE(X) ((string)(X)->query_objective())
#define PRONOUN(X) ((string)(X)->query_pronoun())
#define MORE_ROWS() ((int)this_player()->query_rows())
#define FORCE_SELF(X) command((X),this_player())
#define SORT(X) sort_array((X),"letterorder",this_object())
#define SUB_ARRAY(X,Y) ((X) - (Y))

#define CONFIGURED
#endif

/* Change to 1 if you use TMI-lib */
#if 0

#define HAVE_SPRINTF
#define MOVE(X,Y) move_object(X,Y)
#define NAME(X) ((string)(X)->query("name"))
#define CAP_NAME(X) ((string)(X)->query("cap_name"))
#define ISLIVING(X) (living(X) || userp(X))
#define ISVISIBLE(X) (!((int)(X)->query("invisible")))
#define POSSESSIVE(X) possessive(X)
#define OBJECTIVE(X) objective(X)
#define PRONOUN(X) pronoun(X)
#define MORE_ROWS() ((int)this_player()->getenv("LINES"))
#define FORCE_SELF(X) ((int)this_player()->force_us(X))
#define SORT(X) sort_array((X))
#define USE_UID
#define SUB_ARRAY(X,Y) ((mixed *)(X) - (mnixed *)(Y))

#include <mudlib.h>
#include <config.h>

#define TMI_LIB
#define CONFIGURED
#endif

#ifndef CONFIGURED
/* #define HAVE_SPRINTF */

/* most people have buggy explode, if you don't. comment this out */
#define BUGGY_EXPLODE
#define DEBUG 0

#define replace(X,Y,Z) implode(my_explode(X,Y),Z)

/* Change this to move objects */
#define MOVE(X,Y) move_object(X,Y)
#define NAME(X) lower_case((X)->query_name())
#define CAP_NAME(X) (X)->query_name()
#define ISLIVING(X) living(X)
#define ISVISIBLE(X) (!!((string)(X)->short()))
#define FORCE_SELF(X) command((X),this_player())
#define POSSESSIVE(X) (({"its","his","hers"})[(int)(X)->query_gender(X)])
#define OBJECTIVE(X) (({"it","him","her"})[(int)(X)->query_gender(X)])
#define PRONOUN(X) (({"it","he","she"})[(int)(X)->query_gender(X)])
#define MORE_ROWS() 22
#define SORT(X) sort_array((X),"letterorder",this_object())
#define SUB_ARRAY(X,Y) ((X) - (Y))
#endif


#define SIMP 0
#define DEFA 1
#define DEUX 2
#define PERS 3
#define QUAD 4
#define PREV 5
#define SHRT 6
#define PHYS 7
#define FULL 8


/* if we use the exact same 'spaces' string evewhere we save some memory
 * it also look nicer.
 */
#define SPACES "                                                            "

string *my_explode(string a,string b)
{
#ifdef BUGGY_EXPLODE
  string *c;
  if(a==b) return ({"",""}); 
  if(strlen(b) && a[0..strlen(b)-1]==b)
    return ({ "" })+ my_explode(a[strlen(b)..strlen(a)-1],b);
  if(c=explode(a+b,b)) return c;
  return ({});
#else
  return explode(a,b);
#endif
}

#ifdef HAVE_SPRINTF

/* This linebreak has usually a limit about 10000 bytes */
string fast_linebreak(string text,string pre,int width)
{
  return sprintf("%s%-=*s",pre,width,text);
}

#else /* have_sprintf */

/* This doesn't have to be able to linebreak very large strings */
string fast_linebreak(string text,string pre,int width)
{
  string *parts,pre2;
  int part;

  parts=my_explode(text,"\n");
  pre2=SPACES[1..strlen(pre)];

  for(part=0;part<sizeof(parts);part++)
  {
    string *words,out;
    int word,len;
    
    words=my_explode(parts[part]," ");

    words[0]=pre2+words[0];
    len=strlen(words[0]);
    for(word=1;word<sizeof(words);word++)
    {
      if((len+=strlen(words[word])+1)>=width)
      {
	len=strlen(words[word])+1;
	words[word]="\n"+pre2+words[word];
      }
    }

    parts[part]=implode(words," ");
  }

  return pre+implode(parts,"\n")[strlen(pre)..100000000];
}
#endif /* have_sprintf */

#ifdef LPC4
string big_linebreak(string text,string pre,int width)
{
  return fast_linebreak(text,pre,width);
}
#else /* LPC4 */

/* Standard sprintf has an internal buffer of 10000 bytes. To work around
 * this bug we call fast_linebreak a few times..... This also helps if you
 * don't have sprintf and is linebreaking something that has more words
 * than can be fitted into you arrays.
 */
string big_linebreak(string s,string pre,int width)
{
  int e;
  string done,a,b;

  done="";
  while(strlen(s))
  {
    if(strlen(s)<5000)
    {
      e=5000;
    }else{
      e=5000;
      while(e>=0 && s[e]!=' ') e--;
      if(e==-1) return done+"   "+s+"\n";
    }
    done+=fast_linebreak(s[0..e-1],pre,width);
    pre=SPACES[1..strlen(pre)];
    s=s[e+1..strlen(s)-1];
    for(e=strlen(done)-1;e>=0 && done[e]!='\n';e--);

    a=0;
    b="";
    sscanf(s,"%s %s",a,b);
    while(a && strlen(a)+strlen(done)-e<=width+2)
    {
      done+=" "+a;
      s=b;
      a=0;
      b="";
      sscanf(s,"%s %s",a,b);
    }
    done+="\n";
  }
  return done;
}
#endif /* LPC4 */


int get() { return 1; }
int drop() { return 1; }
int id(string s) { return s=="soul"; }
void move(object x) { move_object(this_object(),x); }

#ifdef MUDOS
mixed *m_indices(mapping m)
{
  return keys(m);
}

mixed *m_values(mapping m)
{
  return values(m);
}

mapping m_delete(mapping m, mixed elem)
{
  map_delete(m, elem);
  return m;
}

int m_sizeof(mapping m)
{
  return sizeof(m);
}

mapping mkmapping(mixed *indices,mixed *values)
{
  mapping tmp;
  int e;

  tmp=allocate_mapping(sizeof(indices));
  for(e=0; e<sizeof(indices); e++)
    tmp[indices[e]] = values[e];
  return tmp;
}

#endif

/* Bullshit or not, you be the judge! */
string share_string(string s)
{
  return m_indices(([s:0]))[0];
}

varargs string implode_nicely(string *dum,string del)
{
  int s;
  if(!del) del="and";
  switch(s=sizeof(dum))
  {
  default:
    return implode(dum[0..s-2],", ")+" "+del+" "+dum[s-1];

  case 2:
    return dum[0]+" "+del+" "+dum[1];

  case 1:
    return dum[0];
  
  case 0:
    return "";
  }
}

string morestring;
void more(string str) { morestring+=str; }

void more_flush(string str)
{
  int e;
  string a;
  int rows;

  rows=MORE_ROWS();
  if (rows<2) rows = 24;
  rows-=2;

  if(str=="q")
  {
    morestring="";
    return;
  }
  for(e=0;e<rows;e++)
  {
    if(sscanf(morestring,"%s\n%s",a,morestring))
    {
      write(a+"\n");
    }else{
      write(morestring);
      e=4711;
      morestring="";
    }
  }
  if(strlen(morestring))
  {
    write("*Press return for more or q to end. >");
    input_to("more_flush");
  }
}

string last_action;
string parsed_part,unparsed_part,uncertain_part;
mixed *brokendown_data;
mapping brokendown_on_person;

mixed *query_brokendown_data() { return brokendown_data; }
string query_last_action() { return last_action; }

mixed *query_feeling_for(object o)
{
  int e,d;
  mixed *tmp;
  /* this way might be slower, but it can take a lot of action */
  if(!brokendown_on_person)
  {
    brokendown_on_person=([]);
    for(e=1;e<sizeof(brokendown_data);e++)
    {
      tmp=brokendown_data[e][1];
      for(d=0;d<sizeof(tmp);d++)
      {
	if(brokendown_on_person[tmp[d]])
	{
	  brokendown_on_person[tmp[d]]+=({brokendown_data[e]});
	}else{
	  brokendown_on_person[tmp[d]]=
	    ({brokendown_data[0],brokendown_data[e]});
	}
      }
    }
  }
  return brokendown_on_person[o];
}

void reset_last_action()
{
  last_action=brokendown_data=brokendown_on_person=0;
}

void set_last_action(string s)
{
  last_action=s+" ";
  brokendown_data=({s});
}

string SOUL;
mapping verbs;

mapping get_verbs()
{
  if(verbs) return verbs;
  return 
    ([
"flex":     ({DEUX,0," flex \nYOUR muscles \nHOW"," flexes \nYOUR muscles \nHOW"}),
"snort":    ({SIMP,0," snort$ \nHOW \nAT"," at"}),
"pant":     ({SIMP,({"heavily"})," pant$ \nHOW \nAT"," at"}),
"hmm":      ({SIMP,0," hmm$ \nHOW \nAT"," at"}),
"ack":      ({SIMP,0," ack$ \nHOW \nAT"," at"}),
"guffaw":   ({SIMP,0," guffaw$ \nHOW \nAT"," at"}),
"raise":    ({SIMP,0," \nHOW raise$ an eyebrow \nAT"," at"}),
"snap":     ({SIMP,0," snap$ \nYOUR fingers \nAT"," at"}),
"lust":     ({DEFA,0,"", " for"}),
"burp":     ({DEFA,({"rudely"}),""," at"}),
"wink":     ({DEFA,({"suggestively"}),""," at"}),
"smile":    ({DEFA,({"happily"}),""," at"}),
"yawn":     ({DEFA,0,""," at"}),
"swoon":    ({DEFA,({"romantically"}),""," at"}),
"sneer":    ({DEFA,({"disdainfully"}),""," at"}),
"beam":     ({DEFA,0,""," at"}),
"point":    ({DEFA,0,""," at"}),
"grin":     ({DEFA,({"evilly"}),""," at"}),
"laugh":    ({DEFA,0,""," at"}),
"nod":      ({DEFA,({"solemnly"}),""," at"}),
"wave":     ({DEFA,({"happily"}),""," at"}),
"cackle":   ({DEFA,({"gleefully"}),""," at"}),
"chuckle":  ({DEFA,0,""," at"}),
"bow":      ({DEFA,0,""," to"}),
"surrender":({DEFA,0,""," to"}),
"capitulate":({DEFA,({"unconditionally"}),""," to"}),
"glare":    ({DEFA,({"stonily"}),""," at"}),
"giggle":   ({DEFA,({"merrily"}),""," at"}),
"groan":    ({DEFA,0,""," at"}),
"grunt":    ({DEFA,0,""," at"}),
"growl":    ({DEFA,0,""," at"}),
"breathe":  ({DEFA,({"heavily"}),""," at"}),
"argh":     ({DEFA,0,""," at"}),
"scowl":    ({DEFA,({"darkly"}),""," at"}),
"snarl":    ({DEFA,0,""," at"}),
"recoil":   ({DEFA,({"with fear"}),""," from"}),
"moan":     ({DEFA,0,""," at"}),
"howl":     ({DEFA,({"in pain"}),""," at"}),
"puke":     ({DEFA,0,""," on"}),
"drool":    ({DEFA,0,""," on"}),
"sneeze":   ({DEFA,({"loudly"}),""," at"}),
"spit":     ({DEFA,0,""," on"}),
"stare":    ({DEFA,0,""," at"}),
"whistle":  ({DEFA,({"appreciatively"}),""," at"}),
"applaud":  ({DEFA,0,"",""}),
"leer":     ({DEFA,0,""," at"}),
"agree":    ({DEFA,0,""," with"}),
"believe":  ({PERS,0," believe$ in \nMYself \nHOW"," believe$ \nWHO \nHOW"}),
"understand":({PERS,({"now"})," understand$ \nHOW"," understand$ \nWHO \nHOW"}),
"disagree": ({DEFA,0,""," with"}),
"fart":     ({DEFA,0,""," at"}),
"dance":    ({DEFA,0,""," with"}),
"flirt":    ({DEFA,0,""," with"}),
"meow":     ({DEFA,0,"", " at"}),
"bark":     ({DEFA,0,"", " at"}),
"ogle":     ({PREV,0,""}),
"pet":      ({SIMP,0," pet$ \nWHO \nHOW \nWHERE"}),
"barf":     ({DEFA,0,"", " on"}),
"purr":     ({DEFA,0,""," at"}),
"curtsey":  ({DEFA,0,""," before"}),
"puzzle":   ({SIMP,0," look$ \nHOW puzzled \nAT"," at"}),
"grovel":   ({DEFA,0,""," before"}),
"listen":   ({DEFA,0,""," to"}),
"tongue":   ({SIMP,0," stick$ \nYOUR tongue out \nHOW \nAT"," at"}),
"apologize":({DEFA,0,""," to"}),
"complain": ({DEFA,0,""," about"}),
"rotate":   ({PERS,0 , " rotate$ \nHOW"," rotate$ \nWHO \nHOW"}),
"excuse":   ({PERS,0," \nHOW excuse$ \nMYself"," \nHOW excuse$ \nMYself to \nWHO"}),
"beg":      ({PERS,0," beg$ \nHOW"," beg$ \nWHO for mercy \nHOW"}),
"fear":     ({PERS,0," shiver$ \nHOW with fear"," fear$ \nWHO \nHOW"}),
"headshake":({SIMP,0," shake$ \nYOUR head \nAT \nHOW"," at"}),
"shake":    ({SIMP,({"like a bowlful of jello"})," shake$ \nAT \nHOW",""}),
"grimace":  ({SIMP,0," \nHOW make$ an awful face \nAT"," at"}),
"stomp":    ({PERS,0," stomp$ \nYOUR foot \nHOW"," stomp$ on \nPOSS foot \nHOW"}),
"snigger":  ({DEFA,({"jeeringly"}),""," at"}),
"watch":    ({QUAD,({"carefully"})," watch the surroundings \nHOW",
		                       " watches the surroundings \nHOW",
				       " watch \nWHO \nHOW",
				       " watches \nWHO \nHOW",}),
"scratch":  ({QUAD,({0,0,"on the head"}),
		     " scratch \nMYself \nHOW \nWHERE",
		     " scratches \nMYself \nHOW \nWHERE",
		     " scratch \nWHO \nHOW \nWHERE",
		     " scratches \nWHO \nHOW \nWHERE",
		   }),
"tap":      ({PERS,({"impatiently",0,"on the shoulder"})," tap$ \nYOUR foot \nHOW"," tap$ \nWHO \nWHERE"}),
"wobble":  ({SIMP,0," wobble$ \nAT \nHOW",""}),
"yodel":   ({SIMP,0," yodel$ a merry tune \nHOW",""}),

/* Message-based verbs */
"curse": ({PERS,0," curse$ \nWHAT \nHOW"," curse$ \nWHO \nHOW"}),
"swear":  ({SIMP,0," swear$ \nWHAT \nAT \nHOW"," before"}),
"criticize": ({PERS,0," criticize$ \nWHAT \nHOW"," criticize$ \nWHO \nHOW"}),
"lie":    ({PERS,0," lie$ \nMSG \nHOW"," lie$ to \nWHO \nHOW"}),
"mutter": ({PERS,0," mutter$ \nMSG \nHOW"," mutter$ to \nWHO \nHOW"}),
"say":   ({SIMP,({0,"'nothing"})," \nHOW say$ \nMSG \nAT"," to"}),
"babble":({SIMP,({"incoherently","'something"})," babble$ \nMSG \nHOW \nAT"," to"}),
"chant":  ({SIMP,({0,"Hare Krishna Krishna Hare Hare"})," \nHOW chant$: \nWHAT",""}),
"sing":  ({SIMP,0," sing$ \nWHAT \nHOW \nAT"," to"}),
"go":    ({DEUX,({0,"ah"})," go \nMSG \nHOW"," goes \nMSG \nHOW"}),
"hiss":  ({QUAD,0,
	     " hiss \nMSG \nHOW"," hisses \nMSG \nHOW",
	     " hiss \nMSG to \nWHO \nHOW"," hisses \nMSG to \nWHO \nHOW",
	 }),
"exclaim":  ({SIMP,0," \nHOW exclaim$ \nAT: \nWHAT!",""}),
"quote":  ({SIMP,0," \nHOW quote$ \nAT \nMSG"," to"}),
"ask":   ({SIMP,0," \nHOW ask$ \nAT: \nWHAT?",""}),
"mumble":({SIMP,0," mumble$ \nMSG \nHOW \nAT"," to"}),
"murmur":({SIMP,0," murmur$ \nMSG \nHOW \nAT"," to"}),
"scream":({SIMP,({"loudly"})," scream$ \nMSG \nHOW \nAT"," at"}),
"yell":({SIMP,({"in a high pitched voice"})," yell$ \nMSG \nHOW \nAT"," at"}),
"utter":({SIMP,({})," \nHOW utter$ \nMSG \nAT"," to"}),

/* Verbs that require a person */
"hide":        ({SIMP,0," hide$ \nHOW behind \nWHO"}),
"finger":      ({SIMP,0," give$ \nWHO the finger"}),
"mercy":       ({SIMP,0," beg$ \nWHO for mercy"}),
"gripe":       ({PREV,0," to"}),
"peer":        ({PREV,0," at"}),
"remember":    ({SIMP,0," remember$ \nAT \nHOW",""}),
"surprise":    ({PREV,0,""}),
"pounce":      ({PHYS,({"playfully"}),""}),
"bite":        ({PERS,0," \nHOW bite$ \nYOUR lip"," bite$ \nWHO \nHOW \nWHERE"}),
"lick":        ({SIMP,0," lick$ \nWHO \nHOW \nWHERE"}),
"caper":       ({PERS,({"merrily"})," caper$ \nHOW about"," caper$ around \nWHO \nHOW"}),
"beep":        ({PERS, ({"triumphantly",0,"on the nose"}),
          " \nHOW beep$ \nMYself \nWHERE"," \nHOW beep$ \nWHO \nWHERE"}),
"blink":       ({PERS,0," blink$ \nHOW"," blink$ \nHOW at \nWHO"}),
"bonk":        ({PHYS,({0,0,"on the head"}),""}),
"bop":         ({PHYS,({0,0,"on the head"}),""}),
"stroke":      ({PHYS,({0,0,"on the cheek"}),""}),
"hold":        ({PHYS,({0,0,"in \nYOUR arms"}),""}),
"embrace":     ({PHYS,({0,0,"in \nYOUR arms"}),""}),
"handshake":   ({SIMP,0," shake$ hands with \nWHO",""}),
"tickle":      ({PREV,0,""}),
"worship":     ({PREV,0,""}),
"admire":      ({PREV,0,""}),
"mock":        ({PREV,0,""}),
"tease":       ({PREV,0,""}),
"taunt":       ({PREV,0,""}),
"strangle":    ({PREV,0,""}),
"hate":        ({PREV,0,""}),
"fondle":      ({PREV,0,""}),
/* "dandle":      ({PREV,0,""}),   In what dictionary can I find this ? */
"squeeze":     ({PREV,({"fondly"}),""}),
"comfort":     ({PREV,0,""}),
"nudge":       ({PHYS,({"suggestively"}),""}),
"slap":        ({PHYS,({0,0,"in the face"}),""}),
"hit":         ({PHYS,({0,0,"in the face"}),""}),
"kick":        ({PHYS,({"hard"}),""}),
"tackle":      ({SIMP,0," tackle$ \nWHO \nHOW",""}),
"spank":       ({PHYS,({0,0,"on the butt"}),""}),
"pat":         ({PHYS,({0,0,"on the head"}),""}),
"punch":       ({DEUX,({0,0,"in the eye"})," punch \nWHO \nHOW \nWHERE"," punches \nWHO \nHOW \nWHERE"}),
"hug":         ({PREV,0,""}),
/* "snog":        ({PREV,0,""}), Not in any dictionary as far as I know */
"want":        ({PREV,0,""}),
"pinch":       ({DEUX,0," pinch \nWHO \nHOW \nWHERE"," pinches \nWHO \nHOW \nWHERE"}),
"kiss":        ({DEUX,0," kiss \nWHO \nHOW \nWHERE"," kisses \nWHO \nHOW \nWHERE"}),
"caress":      ({DEUX,({0,0,"on the cheek"})," caress \nWHO \nHOW \nWHERE"," caresses \nWHO \nHOW \nWHERE"}),
"smooch":      ({DEUX,0," smooch \nWHO \nHOW"," smooches \nWHO \nHOW"}),
"envy":        ({DEUX,0," envy \nWHO \nHOW"," envies \nWHO \nHOW"}),
"touch":       ({DEUX,0," touch \nWHO \nHOW \nWHERE"," touches \nWHO \nHOW \nWHERE"}),
"knee":        ({PHYS,({0,0,"where it hurts"}),""}),
"love":        ({PREV,0,""}),
"adore":       ({PREV,0,""}),
"grope":       ({PREV,0,""}),
"poke":        ({PHYS,({0,0,"in the ribs"}),""}),
"snuggle":     ({PREV,0,""}),
"kneel":       ({SIMP,0," \nHOW fall$ on \nYOUR knees \nAT"," in front of"}),
"trust":       ({PREV,0,""}),
"like":        ({PREV,0,""}),
"greet":       ({PREV,0,""}),
"welcome":     ({PREV,0,""}),
"thank":       ({PREV,0,""}),
"cuddle":      ({PREV,0,""}),
"salute":      ({PREV,0,""}),
"french":      ({SIMP,0," give$ \nWHO a REAL kiss, it seems to last forever"}),
"nibble":      ({SIMP,0," nibble$ \nHOW on \nPOSS ear"}),
"ruffle":      ({SIMP,0," ruffle$ \nPOSS hair \nHOW"}),
"ignore":      ({PREV,0,""}),
"forgive":     ({PREV,0,""}),
"congratulate":({PREV,0,""}),
"ayt":         ({SIMP,0," wave$ \nYOUR hand in front of \nPOSS face, \nIS \nSUBJ \nHOW there?"}),

/* Verbs that don't need, nor use persons */
"roll":   ({SIMP,({"to the ceiling"})," roll$ \nYOUR eyes \nHOW"}),
"boggle": ({SIMP,0," boggle$ \nHOW at the concept"}),
"cheer":  ({SHRT,({"enthusiastically"}),""}),
"twiddle":({SIMP,0," twiddle$ \nYOUR thumbs \nHOW"}),
"wiggle": ({SIMP,0," wiggle$ \nYOUR bottom \nAT \nHOW"," at"}),
"wrinkle":({SIMP,0," wrinkle$ \nYOUR nose \nAT \nHOW"," at"}),
"thumb":  ({SIMP,0," \nHOW suck$ \nYOUR thumb"}),
"flip":   ({SIMP,0," flip$ \nHOW head over heels"}),
"cry":    ({DEUX,0," cry \nHOW"," cries \nHOW"}),
"ah":     ({DEUX,0," go 'ah' \nHOW"," goes 'ah' \nHOW"}),
"clear":  ({SIMP,0," clear$ \nYOUR throat \nHOW"}),
"sob":    ({SHRT,0,""}),
"lag":    ({SHRT,({"helplessly"}),""}),
"whine":  ({SHRT,0,""}),
"cringe": ({SIMP,({"in terror"})," cringe$ \nHOW"}),
"sweat":  ({SHRT,0,""}),
"gurgle": ({SHRT,0,""}),
"grumble":({SHRT,0,""}),
"panic":  ({SHRT,0,""}),
"pace":   ({SIMP,({"impatiently"})," start$ pacing \nHOW"}),
"pale":   ({SIMP,0," turn$ white as ashes \nHOW"}),
"die":    ({DEUX,0," fall \nHOW down and play dead"," falls \nHOW to the ground, dead"}),
"sleep":  ({DEUX,({"soundly"})," fall asleep \nHOW"," falls asleep \nHOW"}),
"stumble":({SHRT,0,""}),
"bounce": ({SHRT,0,""}),
"sulk":   ({SHRT,({"in the corner"}),""}),
"strut":  ({SHRT,({"proudly"}),""}),
"sniff":  ({SHRT,0,""}),
"snivel": ({SHRT,({"pathetically"}),""}),
"snore":  ({SHRT,0,""}),
"clue":   ({SIMP,0," need$ a clue \nHOW"}),
"stupid": ({SIMP,0," look$ \nHOW stupid"}),
"bored":  ({SIMP,0," look$ \nHOW bored"}),
"snicker":({SHRT,0,""}),
"smirk":  ({SHRT,0,""}),
"jump":   ({SIMP,({"up and down in aggravation"}) ," jump$ \nHOW"}),
"squint": ({SHRT,0 ,""}),
"huff":   ({SHRT,0 ,""}),
"puff":   ({SHRT,0 ,""}),
"fume":   ({SHRT,0 ,""}),
"steam":  ({SHRT,0 ,""}),
"choke":  ({SHRT,0 ,""}),
"faint":  ({SHRT,0,""}),
"shrug":  ({SHRT,0,""}),
"pout":   ({SHRT,0,""}),
"hiccup": ({SHRT,0,""}),
"frown":  ({SHRT,0,""}),
"gasp":   ({SHRT,({"in astonishment"}),""}),
"think":  ({SHRT,({"carefully"}),""}),
"ponder": ({SHRT,({"over some problem"}),""}),
"wonder": ({DEFA,0,""," at"}),
"clap":   ({SHRT,0,""}),
"sigh":   ({SHRT,0,""}),
"cough":  ({SHRT,({"noisily"}),""}),
"shiver": ({SHRT,({"from the cold"}),""}),
"tremble":({SHRT,0,""}),
"twitch": ({DEUX,0," twitch \nHOW"," twitches \nHOW"}),
"bitch":  ({DEUX,0," bitch \nHOW"," bitches \nHOW"}),
"blush":  ({DEUX,0," blush \nHOW"," blushes \nHOW"}),
"stretch":({DEUX,0," stretch \nHOW"," stretches \nHOW"}),
"relax":  ({DEUX,0," relax \nHOW"," relaxes \nHOW"}),
"duck":   ({PERS,0," duck$ \nHOW out of the way"," duck$ \nHOW out of \nPOSS way"}),

      ]);
}

/* new class of words, not yet used */
/*
string *adjectives=
({
  "bored",
  "confused",
  "curious",
  "sad",
  "surprised",
  "tired",
})

*/
mapping adverbs;
low_get_adverbs()
{
  string *q,f;
  f=read_file("/"+SOUL+"_adverbs");
  if(f)
    q=my_explode(f,"\n")-({""});
  else
    q=({});
  return q;
}

get_adverbs()
{
  string *q;
  if(adverbs) return adverbs;
  q=low_get_adverbs();
  return mkmapping(q,q);
}

mapping how;
mapping get_how()
{
  if(how) return how;
  return
    ([
      "very":1,
      "quite":1,
      "barely":1,
      "extremely":1,
      "somewhat":1,
      "almost":1,
      ]);
}

mapping bodydata;
mapping get_bodydata()
{
  string *q;
  if(bodydata) return bodydata;
  return
    ([
      "hand":"on the hand",
      "forehead":"on the forehead",
      "head":"on the head",
      "face":"in the face",
      "hurts":"where it hurts",
      "eye":"in the eye",
      "ear":"on the ear",
      "stomach":"in the stomach",
      "butt":"on the butt",
      "behind":"on the behind",
      "leg":"on the leg",
      "foot":"on the foot",
      "toe":"on the right toe",
      "nose":"on the nose",
      "neck":"in the neck",
      "back":"on the back",
      "arm":"on the arm",
      "chest":"on the chest",
      "cheek":"on the cheek",
      "side":"in the side",
      "everywhere":"everywhere",
      "shoulder":"on the shoulder"
      ]);
}

mapping messages;
mapping xverbs;
mapping xadverbs;

TELL_OBJECT(object o,string s)
{
  if(messages[o]) messages[o]+=s;
  else messages[o]=s;
}

tell_room(o,s,a)
{
  if(pointerp(a))
    a=SUB_ARRAY(all_inventory(o),a);
  else
    a=all_inventory(o);
  map_array(a,"TELL_OBJECT",this_object(),s);
}

varargs say(s,o)
{
  tell_room(environment(this_player()),s,({this_player(),o}));
}

string linebreak(string s) { return big_linebreak(s,"   ",75); }

#define WRITE(X) TELL_OBJECT(this_player(),(X))
flush()
{
  int e;
  object *a;
  string *b,msg;
  a=m_indices(messages);
  b=m_values(messages);
  e=sizeof(a);
  while(e--)
  {
    if(a[e])
    {
      msg=b[e];
      if(interactive(a[e]))
      {
	msg=fast_linebreak(msg,"",75);
      }
#ifndef TMI_LIB
      tell_object(a[e],msg);
#else
      message(a[e],msg);
#endif
    }
  }
  messages=([]);
  reset_last_action();
}

void init()
{
  add_action("do_feel","",1);
  add_action("help","help");
  add_action("fail","fail");
  add_action("again","again");
  add_action("dont","don't");
  add_action("dont","dont");
  add_action("feeling","feeling");
  add_action("suddenly","suddenly");
#ifndef TMI_LIB
  remove_call_out("dig");
  call_out("dig",5+random(20));
#endif
}

#ifndef TMI_LIB
void dig()
{
  /* Fel FEL FEL FEL FEL FEL - pen, 930203 */
  /* Nej, helt r{tt t{nkt, men med flera souls blir det lite jobbigt.. */
  /* The golden rules of call_outs: */
  /* Thou shalt have one remove_call_out for each and every call_out! */
  /* There shalt only be one call_out at a time */
  /* Thou shalt NOT have any call outs beside that one */
  /* If thee usest call_outs without obeying these rules, may you in your
     holy mercy SNUFF IT. */

  if(present("soul 2",environment())) return;
  while(this_object() && next_inventory(this_object()))
    MOVE(next_inventory(this_object()),environment(this_object()));
}
#endif

int letterorder(string a,string b)
{
#ifdef MUDOS
  if(a>b) return 1;
  if(a<b) return -1;
#else
  return a>b;
#endif
}

string verb_string;
string get_verb_string()
{
  if(verb_string) return verb_string;
  return verb_string=share_string(linebreak(implode_nicely(SORT(m_indices(verbs)))));
}


string adverb_string; 
string get_adverb_string()
{
#ifndef LOW_EVAL_COST
  if(adverb_string) return adverb_string;
  return adverb_string=share_string(linebreak(implode_nicely(SORT(m_indices(adverbs)))));
#else
  string *q;
  if(adverb_string) return adverb_string;
  q=(string *)low_get_adverbs();
  return adverb_string=share_string(linebreak(implode_nicely(q)));
#endif
}

string xverb_string;
string get_xverb_string()
{
  if(xverb_string) return xverb_string;
  return xverb_string=share_string(linebreak(implode_nicely(SORT(m_indices(xverbs)))));
}


string xadverb_string;
string get_xadverb_string()
{
  if(xadverb_string) return xadverb_string;
  return xadverb_string=share_string(linebreak(implode_nicely(SORT(m_indices(xadverbs)))));
}

void reset()
{
  if(SOUL) return;
  SOUL=file_name(this_object());
  sscanf(SOUL,"/%s",SOUL);
  sscanf(SOUL,"%s#",SOUL);
  verbs=(mapping)SOUL->get_verbs();
  adverbs=(mapping)SOUL->get_adverbs();
  how=(mapping)SOUL->get_how();
  bodydata=(mapping)SOUL->get_bodydata();
  messages=([]);
  xverbs=([]);
  xadverbs=([]);
  morestring="";
  xverb_string="";
  xadverb_string="";
}

void create()
{
#ifdef USE_UID
  seteuid(getuid(this_player()));
#endif
  reset();
}

string globber_one_player(mapping ve);

help(s)
{
  string res;
  if(!s) return 0;
  switch(s)
  {
  case "feelings":
    more("General commands available:\n");
    more(get_verb_string());
    if(m_sizeof(xverbs))
    {
      more("Extra commands available:\n");
      more(get_xverb_string());
    }
    more("grades:\n"+linebreak(implode_nicely(m_indices(how))));
    more("All of these commands can be combinated with 'and' to make it\n");
    more("possible to do several things in several ways to several people.\n");
    more("All feelings can also be prepended with: suddenly, fail, again or dont\n");
    more("Persons and adverbs can be shortened to shorted unique prefix.\n");
    more("See also: help adverbs and help feeling list\n");
    more_flush();
    return 1;

  case "adverbs":
    more("Adverbs that can be used together with feeling-commands:\n");
    more(get_adverb_string());
    more_flush();
    if(m_sizeof(xadverbs))
    {
      more("Extra adverbs available:\n");
      more(get_xadverb_string());
    }
    return 1;

  case "feeling list":
    if(!(res=SOUL->query_total_list()))
    {
      res=globber_one_player(verbs);
      SOUL->set_total_list(res);
      if(m_sizeof(xverbs))
      {
	res+="<TRUNCATED> (try again)\n";
      }
    }else{
      res+=globber_one_player(xverbs);
    }
    res="Verb          Short description\n"+res;
    more(res);
    more_flush();
    return 1;
  case "soul version":
    write("Soul version 1.2, written by hubbe@lysator.liu.se.\n");
    return 1;
  }
}

string get_name(object o) { return NAME(o); }

/* This function should return 1 if the object is a player or monster
 * that is not invisible.
 */
int isplay(object o)
{
  return ISLIVING(o) && ISVISIBLE(o);
}

object *get_persons()
{
  return filter_array(all_inventory(environment(this_player())),
		      "isplay",this_object());
}

mixed prefix(string *dum,string pr,string errm)
{
  string *q;
  int len;

/*  pr=replace(pr,"\\","\\\\");
  pr=replace(pr,"(","\\(");
  pr=replace(pr,")","\\");
  pr=replace(pr,"[","\\[");
  pr=replace(pr,"]","\\[");
  pr=replace(pr,".","\\.");
  pr=replace(pr,"*","\\*");
  pr=replace(pr,"+","\\+");
  pr=replace(pr,"|","\\|"); 
  No need to regexp on wierd characters. Mats 960925
*/
  len = strlen(pr);
  while(len--) 
  {
    if ((pr[len] < 'a' || pr[len] > 'z') && pr[len]!=' ') return 0;
  }
  q=regexp(dum,"^"+pr);
  if (!pointerp(q) || !sizeof(q)) return 0; /* Brom 960415 */
  if(sizeof(q)==1) return q[0];
#ifdef HAVE_SPRINTF
  notify_fail(sprintf("%s\n%-#79s\n",errm,implode(q,"\n")));
#else
  notify_fail(errm+"\n"+linebreak(implode_nicely(q,"or")));
#endif
  return -1;
}


string WHO(object o,object who)
{
  if(who==o)
  {
    if(o==this_player()) 
      return "yourself";
    else
      return "you";
  }else{
    if(o==this_player())
      return OBJECTIVE(o)+"self";
    else
      return CAP_NAME(o);
  }
}

string POSS(object o,object who)
{
  if(who==o)
  {
    if(o==this_player()) 
      return "your own";
    else
      return "your";
  }else{
    if(o==this_player())
      return POSSESSIVE(o)+" own";
    else
    {
      string s;
      s=CAP_NAME(o);
      if(s[strlen(s)-1]=='s') return s+"'"; else return s+"'s";
    }
  }
}

string gloerp(string q,object *t,mixed who,int prev)
{
  string *s,b,mess;
  int e;

  s=my_explode(q,"\n");
  mess=s[0];
  for(e=1;e<sizeof(s);e++)
  {
    if(!prev && sscanf(s[e],"WHO%s",b))
    {
      mess+=implode_nicely(map_array(t,"WHO",this_object(),who))+b;
    }else if(!prev && sscanf(s[e],"POSS%s",b)){
      mess+=implode_nicely(map_array(t,"POSS",this_object(),who))+b;
    }else if(sscanf(s[e],"YOUR%s",b)){
        if(this_player()==who) mess+="your"+b;
        else mess+=POSSESSIVE(this_player())+b;
    }else if(sscanf(s[e],"YOU%s",b)){
        if(this_player()==who) mess+="you"+b;
        else mess+=OBJECTIVE(this_player())+b;
    }else if(sscanf(s[e],"MY%s",b)){
      if(this_player()==who) mess+="your"+b;
      else mess+=OBJECTIVE(this_player())+b;
    }else if(sscanf(s[e],"PRON%s",b)){
      if(this_player()==who) mess+="you"+b;
      else mess+=PRONOUN(this_player())+b;
    }else if(sscanf(s[e],"THEIR%s",b) || (prev && sscanf(s[e],"POSS%s",b))){
      if(sizeof(t)>1)
      {
	if(member_array(who,t)!=-1) mess+="your"+b;
	else mess+="their"+b;
      }else{
	if(t[0]==who)
	  mess+="your"+b;
	else
	  mess+=POSSESSIVE(t[0])+b;
      }
    }else if(sscanf(s[e],"OBJ%s",b) || (prev && sscanf(s[e],"WHO%s",b))){
      if(sizeof(t)>1)
      {
	if(member_array(who,t)!=-1) mess+="all of you"+b;
	else mess+="them"+b;
      }else{
	if(t[0]==who)
	{
	  if(who==this_player())
	    mess+="yourself"+b;
	  else
	    mess+="you"+b;
	}else{
	  if(t[0]==this_player())
	    mess+=OBJECTIVE(this_player())+"self"+b;
	  else
	    mess+=OBJECTIVE(t[0])+b;
	}
      }
    }else if(sscanf(s[e],"SUBJ%s",b)){
      if(sizeof(t)>1)
      {
	if(member_array(who,t)!=-1) mess+="you"+b;
	else mess+="they"+b;
      }else{
	if(t[0]==who)
	  mess+="you"+b;
	else
	  mess+=PRONOUN(t[0])+b;
      }
    }else if(sscanf(s[e],"IS%s",b)){
      if(member_array(who,t)!=-1) mess+="are"+b;
      else if(sizeof(t)<=1) mess+="is"+b; else mess+="are"+b;
    }else{
      mess+="\n"+s[e];
    }
  }
  return mess;
}

/* Output parsed feeling to */
feel(mixed *d,int flag)
{
  int e,w,prev;
  object tp;
  mixed *q;
  q=({});
  for(e=0;e<sizeof(d);e++)
  {
    prev=!sizeof(SUB_ARRAY(q,d[e][0])) && !sizeof(SUB_ARRAY(d[e][0],q)) &&
      -1==member_array(this_player(),q);
    q=d[e][0];
    tell_room(environment(this_player()),
	      gloerp(d[e][3+flag*3],q,0,prev),q+({this_player()}));

    for(w=0;w<sizeof(q);w++)
    {
      if(this_player()!=q[w] && w==member_array(q[w],q))
	TELL_OBJECT(q[w],gloerp(d[e][2+flag*3],q,q[w],prev));
    }

    WRITE(gloerp(d[e][1+flag*3],q,this_player(),prev));

    switch(sizeof(d)-e)
    {
    default:
      tell_room(environment(this_player()),",",({}));
      break;

    case 2:
      tell_room(environment(this_player())," and",({}));
      break;

    case 1:
    case 0:
    }
  }
}

/* This function takes a verb and the arguments given by
 * the user and converts it to an internal representation suitable for passing
 * to feel()
 */
mixed *reduce_verb(string verb,mixed verbdata,object *who,string *adverb,string mess,string *body)
{
  mixed *q;
  string how,a,b,c,d,*aa;
  string where,msg;
  int e;

  if(objectp(verbdata) || stringp(verbdata))
  {
    return (mixed *)verbdata->reduce_verb(verb,who,adverb,mess,body);
  }
  if(pointerp(q=verbdata[1]))
  {
    if(!sizeof(adverb) && sizeof(q)>0 && q[0]) adverb=({q[0]});
    if((!mess || mess=="") && sizeof(q)>1 && q[1])
    {
      mess=q[1];
      if(mess[0]=='\'')
	mess=msg=" "+extract(mess,1);
    }
    if(!sizeof(body) && sizeof(q)>2 && q[2]) body=({q[2]});
  }
  if(!mess || mess=="")
  {
    mess="";
    if(!msg) msg="";
  }else{
    if(!msg) msg=" '"+mess+"'";
    mess=" "+mess;
  }
  where="";
  if(sizeof(body))
    where=" "+implode_nicely(body);

  how=implode_nicely(SUB_ARRAY(adverb,({""})));
  switch(verbdata[0])
  {
  case DEFA:
    if(!a) a=" "+verb+"$ \nHOW \nAT";

  case PREV:
    if(!a) a=" "+verb+"$"+verbdata[2]+" \nWHO \nHOW";

  case PHYS:
   if(!a) a=" "+verb+"$"+verbdata[2]+" \nWHO \nHOW \nWHERE";

  case SHRT:
    if(!a) a=" "+verb+"$"+verbdata[2]+" \nHOW";

  case PERS:
    if(!a) if(sizeof(who)) a=verbdata[3]; else a=verbdata[2];

  case SIMP:
    if(!a) a=verbdata[2];
    if(sizeof(who) && sizeof(verbdata)>3)
    {
      a=replace(a," \nAT",verbdata[3]+" \nWHO");
    }else{
      a=replace(a," \nAT","");
    }

    if(!sizeof(who) && (sscanf(a,"%s\nWHO",c) || 
			sscanf(a,"%s\nPOSS",c) ||
			sscanf(a,"%s\nTHEIR",c) ||
			sscanf(a,"%s\nOBJ",c)))
      return notify_fail("Need person for verb "+verb+".\n"),0;

    if(how=="")
    {
      a=replace(a," \nHOW","");
    }else{
      a=replace(a," \nHOW"," "+how);
    }

    a=replace(a," \nWHERE",where);
    a=replace(a," \nWHAT",mess);
    a=replace(a," \nMSG",msg);
    b=a;

    a=replace(a,"$","");
    b=replace(b,"$","s");
    return ({({who,a,b,b,a,a,a})});

  case DEUX:
    a=verbdata[2];
    b=verbdata[3];
    if(!sizeof(who) && (sscanf(a,"%s\nWHO",c) || 
			sscanf(a,"%s\nPOSS",c) ||
			sscanf(a,"%s\nTHEIR",c) ||
			sscanf(a,"%s\nOBJ",c)))
      return notify_fail("Need person for verb "+verb+".\n"),0;

    a=replace(a," \nWHERE",where);
    b=replace(b," \nWHERE",where);
    a=replace(a," \nWHAT",mess);
    a=replace(a," \nMSG",msg);
    b=replace(b," \nWHAT",mess);
    b=replace(b," \nMSG",msg);
    if(how=="")
    {
      a=replace(a," \nHOW","");
      b=replace(b," \nHOW","");
    }else{
      a=replace(a," \nHOW"," "+how);
      b=replace(b," \nHOW"," "+how);
    }
    return ({({who,a,b,b,a,a,a})});

  case QUAD:
    if(!sizeof(who))
    {
      a=verbdata[2];
      b=verbdata[3];
    }else{
      a=verbdata[4];
      b=verbdata[5];
    }
    a=replace(a," \nWHERE",where);
    b=replace(b," \nWHERE",where);
    a=replace(a," \nWHAT",mess);
    a=replace(a," \nMSG",msg);
    b=replace(b," \nWHAT",mess);
    b=replace(b," \nMSG",msg);
    if(how=="")
    {
      a=replace(a," \nHOW","");
      b=replace(b," \nHOW","");
    }else{
      a=replace(a," \nHOW"," "+how);
      b=replace(b," \nHOW"," "+how);
    }

    return ({({who,a,b,b,a,a,a})});

  case FULL:
    if(!sizeof(who))
    {
      aa=verbdata[2..7];
    }else{
      aa=verbdata[8..13];
    }
    for(e=0;e<sizeof(aa);e++)
    {
      aa[e]=replace(aa[e]," \nWHERE",where);
      aa[e]=replace(aa[e]," \nWHAT",mess);
      aa[e]=replace(aa[e]," \nMSG",msg);
    }

    if(how=="")
    {
      for(e=0;e<sizeof(aa);e++)
	aa[e]=replace(aa[e]," \nHOW","");
    }else{
      for(e=0;e<sizeof(aa);e++)
	aa[e]=replace(aa[e]," \nHOW"," "+how);
    }

    return ({ ({who})+aa });
  }  
}

int query_prevent_shadow() { return 1; }
void long() { write("You can't see it.\n"); }


webster(string t,int offset)
{
  string verb,*q,*adv,*body,tmp,*tmp2,mess;
  int e,u;
  object *who,ob,*people;
  mixed p,*verbdata,*Y;
  mapping persons;
  string _how;
  int except;

  Y=({});
  who=({});
  adv=({});
  body=({});
  mess="";

  q=SUB_ARRAY(my_explode(t," "),({""}));

  for(e=0;e<sizeof(q);e++)
  {
    t=q[e];
#if DEBUG
    write("Webster: q["+e+"]=\""+t+"\"\n");
#endif
    /* Handle message strings, like sing "dum didum di dum do-dum" */
    if(t[0]=='"')
    {
      mess=extract(t,1);
      for(e++;mess[strlen(mess)-1]!='"' && e<sizeof(q);e++) mess+=" "+q[e];
      if(mess[strlen(mess)-1]=='"')
      {
	mess=mess[0..strlen(mess)-2];
	e--;
      }
      continue;
    }

    if(t[strlen(t)-1]==',') t=q[e]=t[0..strlen(t)-2];

    if(how[t])
    {
      _how=t;
      continue;
    }


    switch(t) 
    {
      /* Null words */
    case "and":
    case "&":
    case "":
    case "at":
    case "to":
    case "before":
    case "in":
    case "on":
    case "the":
    case "with":
      break;

    case "me":
    case "myself":
    case "I":
      if(except)
	who=SUB_ARRAY(who,({this_player()}));
      else
	who+=({this_player()});
      break;

    case "them":
    case "him":
    case "her":
    case "it":
      if(!sizeof(Y)) return notify_fail("Who?\n"),0;
      if(t=="them")
      {
	if(sizeof(Y[sizeof(Y)-1][0])<2) return notify_fail("Who?\n"),0;
      }else{
	if(sizeof(Y[sizeof(Y)-1][0])!=1 || OBJECTIVE(Y[sizeof(Y)-1][0][0])!=t)
	  return notify_fail("Who?\n"),0;
      }
      if(except)
	who=SUB_ARRAY(who,Y[sizeof(Y)-1][0]);
      else
	who+=Y[sizeof(Y)-1][0];
      break;

    case "all":
    case "everybody":
    case "everyone":
      if(except)
      {
	who=({});
      }else{
	if(!people) people=get_persons();
	who+=SUB_ARRAY(people,({this_player()}));
      }
      break;

    case "except":
    case "but":
      if(!except && !sizeof(who))
      {
	notify_fail("That '"+t+"' doesn't look grammatically right there.\n");
	return 0;
      }
      except=!except;
      break;

    case "plainly":
      adv=({""});
      break;

    default:
      if((persons && (ob=persons[t])) ||
	 (ob=present(t,environment(this_player()))) && isplay(ob))
      {
	if(except)
	 who=SUB_ARRAY(who,({ob}));
	else
	 who+=({ob});
	break;
      }

      if((p=xverbs[t]) || (p=verbs[t]))
      {
	if(verb)
	{
	  verbdata=reduce_verb(verb,verbdata,who,adv,mess,body);
	  brokendown_data+=({ ({verb,who,adv,mess,body}) });
	  except=0;
	  if(!verbdata) return 0; /* An error was found. */
	  Y+=verbdata;		/* verbdata can be more than one verb */
	  mess="";
	  adv=({});
	  who=({});
	  body=({});
	}
	verb=q[e];
	verbdata=p;
	break;
      }
      if(adverbs[t] || xadverbs[t])
      {
	if(_how)
	{
	  adv+=({_how+" "+t});
	  _how=0;
	}else{
	  adv+=({t});
	}
	break;
      }
      if(p=bodydata[t])
      {
	body+=({p});
	break;
      }

      if(!people) people=get_persons();
      if(!persons) persons=mkmapping(map_array(people,"get_name",this_object()),people);

      if(p=prefix(m_indices(persons),t,"Who do you mean?"))
      {
	if(p==-1)
	{
	  parsed_part=last_action+(e?implode(q[0..e-1]," "):"");
	  uncertain_part=t;
	  unparsed_part=implode(q[e+1..sizeof(q)]," ");
	  last_action="";
	  return 0;
	}
	q[e]=get_name(persons[p]);
	if(except)
	  who=SUB_ARRAY(who,({persons[p]}));
	else
	  who+=({persons[p]});
	break;
      }
      
      u=e;
      tmp=t;
      p=prefix(m_indices(adverbs),tmp,"What adverb was that?");
      while(p==-1 && u+1<sizeof(q))
      {
	u++;
	tmp+=" "+q[u];
	p=prefix(m_indices(adverbs),tmp,"What adverb was that?");
      }

      if(!p)
      {
	u=e;
	tmp=t;
	p=prefix(m_indices(xadverbs),tmp,"What adverb was that?");
	while(p==-1 && u+1<sizeof(q))
	{
	  u++;
	  tmp+=" "+q[u];
	  p=prefix(m_indices(xadverbs),tmp,"What adverb was that?");
	}
      }

      if(p)
      {
	if(p==-1)
	{
	  parsed_part=last_action+(e?implode(q[0..e-1]," "):"");
	  uncertain_part=t;
	  unparsed_part=implode(q[u+1..sizeof(q)]," ");
	  last_action="";
	  return 0;
	}
	tmp2=explode(p," ");
	for(u=0;tmp2 && u<sizeof(tmp2) && e<sizeof(q);u++)
	{
	  if(tmp2[u]==q[e]) { e++; continue; }
	  if(tmp2[u][0..strlen(q[e])-1]==q[e])  e++;
	  break;
	}
	e--;
	if(p=="plainly")
	{
	  adv=({""});
	}else if(_how){
	  adv+=({_how+" "+p});
	  _how=0;
	}else{
	  adv+=({p});
	}
	break;
      }

      switch(offset+e)
      {
      case 1: verb="first"; break;
      case 2: verb="second"; break;
      case 3: verb="third"; break;
      case 4: verb="fourth"; break;
      case 5: verb="fifth"; break;
      case 6: verb="sixth"; break;
      case 7: verb="seventh"; break;
      case 8: verb="eigth"; break;
      case 9: verb="ninth"; break;
      case 10: verb="tenth"; break;
      case 11: verb="eleventh"; break;
      case 12: verb="twelvth"; break;
      default:
	switch((offset+e)%10)
	{
	case 1: verb=(offset+e)+"st"; break;
	case 2: verb=(offset+e)+"nd"; break;
	case 3: verb=(offset+e)+"rd"; break;
	default: verb=(offset+e)+"th"; break;
	}
      }
      notify_fail("The "+verb+" word in that sentence doesn't make sense to me.\n");
      return 0;
    }
  }
  if(!verb)
  {
    notify_fail("No verb?\n");
    return 0;
  }
  verbdata=reduce_verb(verb,verbdata,who,adv,mess,body);
  brokendown_data+=({ ({verb,who,adv,mess,body}) });
  if(!verbdata) return 0; /* An error was found. */
  last_action+=implode(q," ");
  Y+=verbdata; /* verbdata can be more than one verb */
  return Y;
}

do_feel(string p)
{
  string v;
  mixed *q;
  int e;
  v=query_verb();
  if(uncertain_part)
  {
    if(uncertain_part==v[0..strlen(uncertain_part)-1] &&
       strlen(uncertain_part)<strlen(v))
    {
      parsed_part+=" "+(p?v+" "+p:v)+" "+unparsed_part;
      uncertain_part=0;
      while(sscanf(parsed_part," %s",parsed_part));
      FORCE_SELF(parsed_part);
      return 1;
    }else{
      uncertain_part=0;
    }
  }
  if(!verbs[v] && !xverbs[v]) return 0;
  if(v=="say") return 0;
  if(p) v+=" "+p;
  set_last_action("");
  if(!(q=webster(v,1))) return 0;
  if(!q) return notify_fail("Hmm, what?\n"),0;
  messages=([]);
  WRITE("You");
  say(CAP_NAME(this_player()));
  feel(q,0);
  v=messages[this_player()];
  e=v[strlen(v)-1];
  if(e!='.' && e!='?' && e!='!')
    tell_room(environment(this_player()),".\n");
  else
    tell_room(environment(this_player()),"\n");
  flush(); 
  return 1;
}

suddenly(string p)
{
  string v;
  mixed *q;
  int e;
  if(!p)
  {
    write("Suddenly what?\n");
    return 1;
  }
  set_last_action("suddenly");
  if(!(q=webster(p,2))) return 0;
  if(!q) return write("Hmm, what?\n"),1;
  messages=([]);

  WRITE("Suddenly, you");
  say("Suddenly, "+CAP_NAME(this_player()));
  feel(q,0);
  v=messages[this_player()];
  e=v[strlen(v)-1];
  if(e!='.' && e!='?' && e!='!')
    tell_room(environment(this_player()),".\n");
  else
    tell_room(environment(this_player()),"\n");
  flush();
  return 1;
}

again(string p)
{
  string v;
  mixed *q;
  
  if(!p)
  {
    write("Do what again?\n");
    return 1;
  }
  set_last_action("again");
  if(!(q=webster(p,2))) return 0;
  if(!q) return write("Hmm, what?\n"),1;
  messages=([]);

  WRITE("You");
  say(CAP_NAME(this_player()));
  feel(q,0);
  tell_room(environment(this_player())," again.\n");
  flush();
  return 1;
}

fail(string p)
{
  string v;
  mixed *q;
  
  if(!p)
  {
    write("Fail with what?\n");
    return 1;
  }
  set_last_action("fail");
  if(!(q=webster(p,2))) return 0;
  if(!q) return write("Hmm, what?\n"),1;
  messages=([]);
  
  WRITE("You try to");
  say(CAP_NAME(this_player())+" tries to");
  feel(q,1);
  WRITE(", but fail miserably.\n");
  say(", but fails miserably.\n");
  flush();
  return 1;
}


dont(string p)
{
  string v;
  mixed *q;
  
  if(!p)
  {
    write("Don't do what?\n");
    return 1;
  }
  set_last_action("dont");
  if(!(q=webster(p,2))) return 0;
  if(!q) return write("Hmm, what?\n"),1;
  messages=([]);
  
  WRITE("You try not to");
  say(CAP_NAME(this_player())+" tries not to");
  feel(q,1);
  WRITE(", but fail miserably.\n");
  say(", but fails miserably.\n");
  flush();
  return 1;
}

feeling(string p)
{
  string v;
  mixed *q;
  int e;
  
  if(!p)
  {
    write("What feeling?\n");
    return 1;
  }
  set_last_action("feeling");
  if(!(q=webster(p,2))) return 0;
  if(!q) return write("Hmm, what?\n"),1;
  messages=([]);

  WRITE("You");
  say(CAP_NAME(this_player()));
  feel(q,0);
  v=messages[this_player()];
  e=v[strlen(v)-1];
  if(e!='.' && e!='?' && e!='!')
    tell_room(environment(this_player()),".\n");
  else
    tell_room(environment(this_player()),"\n");
  flush();
  return 1;
}


/* Takes an array of verbs, only removes extra verbs */
void remove_verb(string *v)
{
  int e;
  for(e=0;e<sizeof(v);e++) xverbs=m_delete(xverbs,v[e]);
  xverb_string=0;
}

/* Takes an array of verbs that follow the same format as the one in the
 * beginning of this file. Here is a short explanation of the components:
 * ([ "verb":([verb_type,defaults,data...})
 * verb_type is one of the defines in the beginning, you have to look
 *   at the examples to what they actually do.
 * defaults is zero or an array containing:
 *        ({defaultadverb,defaultwhat,defaultbodypart})
 * Data has to do with what type of verb it is, again: see the examples,
 *  there should be enogh of them.
 */

add_verb(mapping v)
{
/*  log_file("Feelings",implode_nicely(m_indices(v))+"\n"); */
  remove_verb(m_indices(xverbs) & m_indices(v));
  xverbs+=v;
  xverb_string=0;
}

remove_adverb(string *v)
{
  v=SUB_ARRAY(m_indices(xadverbs),v);
  xadverbs=mkmapping(v,v);
  xadverb_string=0;
}

/* Takes an array of adverbs */
add_adverb(string *v)
{
/*  log_file("Adverbs",implode_nicely(v)+"\n"); */
  v=SUB_ARRAY(v,m_indices(xadverbs));
  xadverbs+=mkmapping(v,v);
  xadverb_string=0;
}

mapping query_xadverbs() { return xadverbs; }
mapping query_xverbs() { return xverbs; }

feel_to_this_player(mixed *d,int flag)
{
  int e,w,prev;
  object tp;
  mixed *q;
  string res;
  res="";
  q=({});
  for(e=0;e<sizeof(d);e++)
  {
    prev=!sizeof(SUB_ARRAY(q,d[e][0])) && !sizeof(SUB_ARRAY(d[e][0],q)) &&
      -1==member_array(this_player(),q);
    q=d[e][0];

    res+=gloerp(d[e][1+flag*3],q,this_player(),prev);

    switch(sizeof(d)-e)
    {
    default:
      res+=",";
      break;

    case 2:
      res+=" and";
      break;

    case 1:
    case 0:
    }
  }
  return res;
}

string total_list;

query_total_list() { return total_list; }

void set_total_list(string s)
{
  if(file_name(previous_object())[0..strlen(SOUL)-1]==SOUL)
    total_list=share_string(s);
}


string globber_one_player(mapping ve)
{
  string *foo,v,res;
  mixed *bar,*q;
  int e,t;

  foo=m_indices(ve);
  bar=m_values(ve);
  res="";
  
  for(e=0;e<sizeof(foo);e++)
  {
    q=reduce_verb(foo[e],bar[e],({}),({}),"",({}));
    if(!q)
    {
      q=reduce_verb(foo[e],bar[e],({this_player()}),({}),"",({}));
    }
    if(!q) continue; /* Maybe I should write 'disabled' or something */
    messages=([]);
    v=foo[e]+"              "[strlen(foo[e])..12]+":You";
    v+=(mixed)feel_to_this_player(q,0);
    t=v[strlen(v)-1];
    if(t!='.' && t!='?' && t!='!')
      res+=v+".\n";
    else
      res+=v+"\n";
  }
  return res;
}
