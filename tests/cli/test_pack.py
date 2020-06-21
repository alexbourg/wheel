import os
from zipfile import ZipFile

import pytest

from wheel.cli.pack import pack

THISDIR = os.path.dirname(__file__)
TESTWHEEL_NAME = 'test-1.0-py2.py3-none-any.whl'
TESTWHEEL_PATH = os.path.join(THISDIR, '..', 'testdata', TESTWHEEL_NAME)


@pytest.mark.filterwarnings('error:Duplicate name')
@pytest.mark.parametrize('build_tag_arg, existing_build_tag, filename', [
    (None, None, 'test-1.0-py2.py3-none-any.whl'),
    ('2b', None, 'test-1.0-2b-py2.py3-none-any.whl'),
    (None, '3', 'test-1.0-3-py2.py3-none-any.whl'),
    ('', '3', 'test-1.0-py2.py3-none-any.whl'),
], ids=['nobuildnum', 'newbuildarg', 'oldbuildnum', 'erasebuildnum'])
def test_pack(tmp_path_factory, tmp_path, build_tag_arg, existing_build_tag, filename):
    unpack_dir = tmp_path_factory.mktemp('wheeldir')
    with ZipFile(TESTWHEEL_PATH) as zf:
        old_record = zf.read('test-1.0.dist-info/RECORD')
        old_record_lines = sorted(line.rstrip() for line in old_record.split(b'\n')
                                  if line and not line.startswith(b'test-1.0.dist-info/WHEEL,'))
        zf.extractall(str(unpack_dir))

    if existing_build_tag:
        # Add the build number to WHEEL
        wheel_file_path = unpack_dir / 'test-1.0.dist-info' / 'WHEEL'
        wheel_file_content = wheel_file_path.read_bytes()
        assert b'Build' not in wheel_file_content
        wheel_file_content += b'Build: 3\r\n'
        wheel_file_path.write_bytes(wheel_file_content)

    pack(str(unpack_dir), str(tmp_path), build_tag_arg)
    new_wheel_path = tmp_path / filename
    assert new_wheel_path.isfile()

    with ZipFile(str(new_wheel_path)) as zf:
        new_record = zf.read('test-1.0.dist-info/RECORD')
        new_record_lines = sorted(line.rstrip() for line in new_record.split(b'\n')
                                  if line and not line.startswith(b'test-1.0.dist-info/WHEEL,'))

        new_wheel_file_content = zf.read('test-1.0.dist-info/WHEEL')

    assert new_record_lines == old_record_lines

    expected_build_num = build_tag_arg or existing_build_tag
    if expected_build_num:
        assert ('Build: %s\r\n' % expected_build_num).encode() in new_wheel_file_content
    else:
        assert b'Build: ' not in new_wheel_file_content
