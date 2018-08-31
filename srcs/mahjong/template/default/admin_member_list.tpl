<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/common.js"></script>
      <div class="block">
                %include admin_frame_header
                <div class="content">
                    %include search
                    <table id="dataTable" class="table table-bordered table-hover"></table>
                </div>
</div>
<script type="text/javascript">
    var pageNumber;
    $('#btn_search').click(function(){
          $('#dataTable').bootstrapTable('refresh');        
   });

    $('#dataTable').bootstrapTable({
          method: 'get',
          url: '{{info["listUrl"]}}',
          contentType: "application/json",
          datatype: "json",
          cache: false,
          striped: true,
          toolbar:'#toolbar',
          pagination: true,
          pageSize: 15,
          pageNumber:parseInt("{{info['cur_page']}}"),
          pageList: [15, 50, 100],
          queryParamsType:'',
          sidePagination:"server",
          minimumCountColumns: 2,
          clickToSelect: true,
          //smartDisplay: true,
          responseHandler:responseFun,
          queryParams:getSearchP,
          onSort:getCellSortByClick,
          //sortOrder: 'asc',
          //sortable: true,                     //是否启用排序
          // exportOptions:{fileName: "{{info['title']}}"+"_"+ new Date().Format("yyyy-MM-dd")},
          columns: [
          [
                {
                    "halign":"center",
                    "align":"center",
                    "class":'count',
                    "colspan": 12
                }
          ],

          [{
              field: 'id',
              title: '用户编号',
              align: 'center',
              valign: 'middle',
              sortable: true
          },{
              field: 'name',
              title: '用户名称',
              align: 'center',
              valign: 'middle'

          },{
              field: 'relate',
              title: '账号ID',
              align: 'center',
              valign: 'middle',
              formatter: getRelater,
          },
          {
              field: 'nickname',
              title: '微信名称',
              align: 'center',
              valign: 'middle'
          },{
              field: 'headImgUrl',
              title: '微信头像',
              align: 'center',
              valign: 'middle',
              formatter:getAvatorImg,
          },{
              field: 'parentAg',
              title: '公会号',
              align: 'center',
              valign: 'middle',
              sortable: true
          },{
              field: 'topAgent',
              title: '顶级公会',
              align: 'center',
              valign: 'middle',
              sortable: true
          },{
              field: 'gid',
              title: '渠道',
              align: 'center',
              valign: 'middle',
              sortable: true
          },{
              field: 'level',
              title: '玩家等级',
              align: 'center',
              valign: 'middle',
              sortable: true
          }
          ,{
              field: 'last_login_date',
              title: '最近登录时间',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },{
              field: 'last_logout_date',
              title: '最近登出时间',
              align: 'center',
              valign: 'middle',
              sortable: true,
          },
          {
              field: 'op',
              title: '操作',
              align: 'center',
              valign: 'middle',
              formatter:getOp
          }]]
    });
      
      function getRelater(value, row, index) {
       
            var dom = "";
            console.log(value);
            $.each(value, function(k, v){
                dom += v ;
            });
            return dom;
      }

      function status(value,row,index){
          eval('var rowobj='+JSON.stringify(row))
          var statusstr = '';
          if(rowobj['open_auth'] == '1'){
              statusstr = '<span class="label label-success">是</span>';
          }else if(rowobj['open_auth'] == '0'){
              statusstr = '<span class="label label-danger">否</span>';
          }

          return [
              statusstr
          ].join('');
      }

      function is_valid(value,row,index){
          eval('var rowobj='+JSON.stringify(row))
          var statusstr = '';
          if(rowobj['valid'] == '1'){
              statusstr = '<span class="label label-success">正常</span>';
          }else if(rowobj['valid'] == '0'){
              statusstr = '<span class="label label-danger">冻结</span>';
          }

          return [
              statusstr
          ].join('');
      }

      function getCellSortByClick(name,sort){ //用于服务端排序重写

          console.log(String.format('------getCellSortByClick name[{0}] sort[{1}]',name,sort));
          $('#dataTable').bootstrapTable('refresh',{'url':String.format('{0}&sort_name={1}&sort_method={2}','{{info["listUrl"]}}',name,sort)});
      }

      function getOp(value,row,index){
          var comfirmUrls = [
              '/admin/member/kick',
              '/admin/member/freeze/fish',
              '/admin/member/freeze/hall',
              '/admin/member/open_auth'
          ];

          var notShowOp = [
                '/admin/member/open_auth',
                '/admin/member/modify',
          ];

          eval('rowobj='+JSON.stringify(row))
          var opList = []
          for (var i = 0; i < rowobj['op'].length; ++i) {
              var op = rowobj['op'][i];
              var str = JSON.stringify({id : rowobj['id'],cur_size:"{{info['cur_size']}}",cur_page:pageNumber});
              var cStr = str.replace(/\"/g, "@");
              %if info.has_key('fish'):
                  if (notShowOp.indexOf(op['url'])>=0){
                      continue;
                  }
              %end
              if(comfirmUrls.indexOf(op['url'])>=0)
                  opList.push(String.format("<a href=\"#\" class=\"btn btn-primary btn-sm\" onclick=\"comfirmDialog(\'{0}\', \'{1}\', \'{2}\')\">{3}</a> ", op['url'], op['method'], cStr, op['txt']));
              else
                  opList.push(String.format("<a href=\"{0}/{5}?id={1}&page_size={2}&cur_page={3}\" class=\"btn btn-primary btn-sm\" > {4} </a> ", op['url'],rowobj['id'],"{{info['cur_size']}}",pageNumber,op['txt'],"{{info['remove_type']}}"));
          }
          console.log(row);
          var user_id = row.id
          var agent_id = row.parentAg
          var topAgent = row.topAgent
          var level = row.level
          opList.push(
          "<button class='btn btn-green clearUserstatus' user_id='"+user_id+"' agent_id='"+ agent_id+"' topAgent='"+topAgent+"' level='"+level+"'>清除用户公会状态</button>"
          )
          return opList.join('');
      }

      //定义列操作
      function getSearchP(p){
        var searchId = $("#searchId").val();
        console.log(p);
        sendParameter = p;
        sendParameter['searchId'] = searchId;

        return sendParameter;
      }

      function responseFun(res){
          count= res.total;
          //实时刷
          $('.count').text(String.format("会员总人数:{0}",count));
          pageNumber = parseInt(res.pageNumber);
          return {"rows": res.result,
                  "total": res.total
          };
      }

      function responseError(status) {
          location.reload();
      }

      $("body").delegate(".clearUserstatus", "click", function(){
        var user_id = $(this).attr("user_id");
        var agent_id = $(this).attr("agent_id");
        var topAgent = $(this).attr("topAgent");
        var level = $(this).attr("level");

        layer.confirm('是否清除用户当前的公户状态？', {
          btn: ['确认','取消'] //按钮
        }, function(){
            
            $.ajax({
                type: 'POST',
                url: "/admin/member/clearAgentStatus",
                data: {"user_id": user_id, "agent_id": agent_id, "agent_id": agent_id, "topAgent": topAgent, "level": level},
                dataType: "json",
                success: function(res, data){
                    layer.msg(res.msg, {icon: 1});
                    location.reload();
                },
                error: function(res, data){
                    console.log(res);
                }, 
            });

            //layer.msg('已经清除', {icon: 1});
        }, function(){
          return;
        });
      });

</script>
%rebase admin_frame_base
