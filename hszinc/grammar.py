#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc grammar specification.
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si: 

from parsimonious.grammar import Grammar

# Grammar according to http://project-haystack.org/doc/Zinc
zinc_grammar = Grammar(r'''
        grid        =   gridMeta cols row*
        nl          =   "\n" / "\r\n"
        gridMeta    =   ver meta? nl
        ver         =   "ver:" str
        meta        =   ( " " metaItem )+
        metaItem    =   metaPair / metaMarker
        metaMarker  =   id
        metaPair    =   id ":" " "* scalar
        valueSep    =   " "* "," " "*
        cols        =   col ( valueSep col )* nl
        col         =   id meta?
        row         =   cell ( valueSep cell )* nl
        cell        =   scalar?
        id          =   alphaLo ( alphaLo / alphaHi / digit / "_" )*
        scalar      =   ref / bin / str / uri / dateTime / date / time / coord / number / null / marker / remove / bool
        null        =   "N"
        marker      =   "M"
        remove      =   "R"
        bool        =   "T" / "F"
        bin         =   "Bin(" binChar* ")"
        binChar     =   ~r"[\x20-\x27\x2a-\x7f]"
        ref         =   "@" refChar* ( " " str )?
        refChar     =   alpha / digit / "_" / ":" / "-" / "." / "~"
        str         =   "\"" strChar* "\""
        uri         =   "`" uriChar* "`"
        strChar     =   ~r"([^\x00-\x1f\\\"]|\\[bfnrt\\\"$]|\\u[0-9a-fA-F]{4})"
        uriChar     =   ~r"([^\x00-\x1f\\`]|\\[bfnrt\\:/?#\[\]@&=;`]|\\u[0-9a-fA-F]{4})"
        number      =   quantity / decimal / "INF" / "-INF" / "NaN"
        decimal     =   "-"? digits ( "." digits )? exp?
        quantity    =   decimal unit
        plusMinus   =   "+" / "-"
        exp         =   ( "e" / "E" ) plusMinus? digits
        unit        =   unitChar+
        unitChar    =   ~r"[^\x00-\x20,]"
        dateTime    =   isoDateTime ( " "+ timeZoneName )?
        isoDateTime =   date dateSep time tzHHMMOffset?
        date        =   digit digit digit digit "-" digit digit "-" digit digit
        time        =   digit digit ":" digit digit ":" digit digit ( "." digit+ )?
        dateSep     =   "t" / "T"
        timeZoneName=   tzUTCOffset / tzName
        tzUTCGMT    =   "UTC" / "GMT"
        tzUTCOffset =   tzUTCGMT ( "0" / ( plusMinus digit+ ) )?
        tzName      =   alphaHi tzNameChar*
        tzNameChar  =   alpha / digit / "_" / "-"
        tzHHMMOffset=   ~r"([zZ]|[+\-]\d{2}:?\d{2})"
        coord       =   "C(" " "* coordDeg valueSep coordDeg " "* ")"
        coordDeg    =   "-"? digits? ( "." digits )?
        alphaLo     =   ~r"[a-z]"
        alphaHi     =   ~r"[A-Z]"
        alpha       =   alphaLo / alphaHi
        digit       =   ~r"[0-9]"
        digits      =   digit ( digit / "_" )*
''')
