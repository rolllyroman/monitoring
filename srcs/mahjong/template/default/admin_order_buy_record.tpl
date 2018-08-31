<script type="text/javascript" src="{{info['STATIC_ADMIN_PATH']}}/js/refreshDateInit.js"></script>
<div class="cl-mcont">
  <div class="block">
            <div class="header">              
              <h3>
                %if info.get('title',None):
                  {{info['title']}}
                %end
              </h3>
            </div>
            <div class="content">
               %include original_search_bar
               <table id="dataTable" class="table table-bordered table-hover"></table>
               成功总额：<span class="allMemonySuccess" style="color: red;">0</span>
               失败总额：<span class="allMemonyFaild" style="color: red;">0</span>
            </div>
  </div>
</div>
<script type="text/javascript">
  var firstDate=new Date();
  firstDate.setDate(firstDate.getDate()-6);
  $('#pick-date-start').val(firstDate.Format("yyyy-MM-dd"));
  $('#pick-date-end').val(new Date().Format("yyyy-MM-dd"));
  
  /**------------------------------------------------
    *  代理操作日志
    -------------------------------------------------
  */
  function initTable() {
      startDate = $("#pick-date-start").val();
      endDate   = $("#pick-date-end").val();
        $("#dataTable").bootstrapTable({
              url: "{{info['tableUrl']}}",
              method: 'get',
              pagination: true,
              pageSize: 15,
              search: true,
              showExport: true,
              exportTypes:['excel', 'csv', 'pdf', 'json'],
              showRefresh: true,
              pageList: [15, 25],
              responseHandler:responseFun,
              queryParams:getSearchP,
              showFooter: true,
              columns: [{
                  field: 'order_no',
                  sortable: true,
                  align: 'center',
                  valign: 'middle',
                  title: '订单编号'
              },{
                  field: 'account',
                  sortable: true,
                  align: 'center',
                  valign: 'middle',
                  title: '账号ID'
              },{
                  field: 'user_name',
                  sortable: true,
                  align: 'center',
                  valign: 'middle',
                  title: '用户名称'
              },
              {
                  field: 'id',
                  sortable: true,
                  align: 'center',
                  valign: 'middle',
                  title: '用户ID'
              },{
                  field: 'agent_id',
                  align: 'center',
                  valign: 'middle',
                  title: '代理ID'
              },{
                  field: 'top_agent',
                  align: 'center',
                  valign: 'middle',
                  title: '一级代理'
              },{
                  field: 'gid',
                  align: 'center',
                  valign: 'middle',
                  title: '渠道'
              },{
                  field: 'bill_time',
                  align: 'center',
                  valign: 'middle',
                  title: '支付时间'
              },{
                  field: 'create_time',
                  align: 'center',
                  valign: 'middle',
                  title: '创建时间'
              }, {
                  field: 'consume',
                  title: '消费点',
                  align: 'center',
                  sortable: true,
                  valign: 'middle',
              },{
                  field: 'pre_balance',
                  title: '消费前',
                  align: 'center',
                  sortable: true,
                  valign: 'middle',
              },{
                  field: 'after_balance',
                  title: '消费后',
                  align: 'center',
                  sortable: true,
                  valign: 'middle',
                  footerFormatter:function(values){
                      return '总消费'
                  }
              },{
                  field: 'balance',
                  title: '消费',
                  align: 'center',
                  sortable: true,
                  valign: 'middle',
                  footerFormatter:function(values){
                      var count = 0 ;
                      for (var val in values)
                          count+=parseFloat(values[val].balance)
                      return count.toFixed(2)
                  }
              },
              {
                  field: 'status', 
                  align: 'center',
                  valign: 'middle',
                  title: '支付状态',
                  formatter: getStatus
              }],
              onSearch: function(index, row, $detaol){
                    console.log(index)
                    console.log(row)
                    console.log($detaol)
              },

              //注册加载子表的事件。注意下这里的三个参数！
              onExpandRow: function (index, row, $detail) {
                  console.log(index,row,$detail);
                  InitSubTable(index, row, $detail);
              }
    });


  function status(value,row,index){
      eval('var rowobj='+JSON.stringify(row))
      var statusstr = '';
      if(rowobj['status'] == '0'){
          statusstr = '<span class="label label-danger">卖钻方未确认</span>';
      }else if(rowobj['status'] == '1'){
          statusstr = '<span class="label label-success">卖钻方已确认</span>';
      }

      return [
          statusstr
      ].join('');
  }

  function getStatus(value,row,index){
        
        if (value == 1) {
            return "<span class='label label-info'> 成功</span>"
        } else {
            return "<span class='label label-danger'> 失败</span>"
        }

  } 

  function getSearchP(p){
          startDate = $("#pick-date-start").val();
          endDate   = $("#pick-date-end").val();

          sendParameter = p;

          sendParameter['startDate'] = startDate;
          sendParameter['endDate']  = endDate;

          return sendParameter;
  }

  function getOp(value,row,index){
        eval('rowobj='+JSON.stringify(row))
        var opList = []
        for (var i = 0; i < rowobj['op'].length; ++i) {
            var op = rowobj['op'][i];
            var str = JSON.stringify({orderNo : rowobj['orderNo']});
            var cStr = str.replace(/\"/g, "@");
            var param = rowobj['orderNo'] ;
            if(op['url'] == '/admin/order/cancel')
            {     
                  if (rowobj['status'] == '1')
                      continue;
                  var contentUrl = op['url'];
                  opList.push(String.format("<a href=\"#\" class=\"btn btn-primary btn-sm\" onclick=\"cancelOrderDialog(\'{0}\',\'{1}\',\'{2}\')\"><i class=\"glyphicon glyphicon-edit\"> {3} </i></a> ",contentUrl, op['method'],cStr,op['txt']));
            }
        }
        return opList.join('');
  }

  //获得返回的json 数据
  function responseFun(res){
      $('.allMemonySuccess').html(res.consumeSucces);
      $(".allMemonyFaild").html(res.consumeFaild);
      return res.data;
  }


}
</script>
%rebase admin_frame_base