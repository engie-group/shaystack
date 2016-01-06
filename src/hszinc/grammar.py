#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc grammar specification.
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si: 

from parsimonious.grammar import Grammar

# Grammar according to http://project-haystack.org/doc/Zinc
zinc_grammar = Grammar(r'''
        grids       =   grid ( nl grid )*
        grid        =   gridMeta cols row*
        nl          =   "\n" / "\r\n"
        gridMeta    =   ver meta? nl
        ver         =   "ver:" str
        meta        =   ( " " metaItem )+
        metaItem    =   metaPair / metaMarker
        metaMarker  =   id
        metaPair    =   id ":" scalar
        cols        =   col ( "," " "* col )* nl
        col         =   id meta?
        row         =   cell ( "," " "* cell )* nl
        cell        =   scalar?
        id          =   alphaLo ( alphaLo / alphaHi / digit / "_" )*
        scalar      =   null / marker / bool / ref / bin / str / uri / date / time / dateTime / coord / number
        null        =   "N"
        marker      =   "M"
        bool        =   "T" / "F"
        bin         =   "Bin(" binChar* ")"
        binChar     =   ~r"[\x20-\x28\x30-\x7f]"
        ref         =   "@" refChar* ( " " str )?
        refChar     =   alpha / digit / "_" / ":" / "-" / "." / "~"
        str         =   "\"" strChar* "\""
        uri         =   "`" uriChar* "`"
        strChar     =   unicodeChar / strEscChar
        uriChar     =   unicodeChar / uriEscChar
        unicodeChar =   ~r"[\x20\x21\x23-\x59\x61-\xff]"
        strEscChar  =   "\\b" / "\\f" / "\\n" / "\\r" / "\\r" / "\\t" / "\\\"" / "\\\\" / "\\$" / uEscChar
        uriEscChar  =   "\\:" / "\\/" / "\\?" / "\\#" / "\\[" / "\\]" / "\\@" / "\\\\" / "\\&" / "\\=" / "\\;" / uEscChar
        uEscChar    =   "\\u" hexDigit hexDigit hexDigit hexDigit
        number      =   quantity / decimal / "INF" / "-INF" / "NaN"
        decimal     =   "-"? digits ( "." digits )? exp?
        quantity    =   decimal unit
        exp         =   ( "e" / "E" ) ( "+" / "-" )? digits
        unit        =   unitChar*
        unitChar    =   alpha / "%" / "_" / "/" / "$"
        date        =   digit digit digit digit "-" digit digit "-" digit digit
        time        =   digit digit ":" digit digit ":" digit digit ( "." digit+ )?
        dateTime    =   date "T" time ( "z" / "Z" / ( " " timeZone ) )
        timeZone    =   ( ( "UTC" / "GMT" ) ( "+" / "-" ) digit+ ) / ( alpha / digit / "_" )+
        coord       =   "C(" coordDeg "," coordDeg ")"
        coordDeg    =   "-"? digits ( "." digits )?
        alphaLo     = ~r"[a-z]"
        alphaHi     = ~r"[A-Z]"
        alpha       = alphaLo / alphaHi
        digit       = ~r"[0-9]"
        digits      = digit ( digit / "_" )*
        hexDigit    = ~r"[a-fA-F0-9]"
''')
