#!/usr/bin/env hub

__main__ = "main"


def foo(hub):
    print("-" * 80)
    print(hub.OPT.test)
    print("-" * 80)


def main(hub):
    hub._.foo()
