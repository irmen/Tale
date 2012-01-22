
def join(words, conj="and"):
    """
    This function joins a list of words to a semantically correct
    list in English. That is, ({"green","red","blue"}) will be joined
    to "green, red, or blue" if 'conj' is "or" (default is "and").
    """
    if len(words)==1:
        return words[0]
    result = ", ".join(words[:-1])
    return result if len(words)<=1 else "%s %s %s" % (result, conj, words[-1])
